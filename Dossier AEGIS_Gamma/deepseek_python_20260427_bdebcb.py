"""
AEGIS-Γ - Module Cartographe de brouillage
"""

import re
from typing import Dict, List, Optional, Set
import numpy as np

from aegis_gamma.core.enums import TypeOpacite, TypeSource, TypeTension, _TYPE_SOURCE_LOOKUP
from aegis_gamma.core.models import FragmentNarratif, ZoneDeTension
from aegis_gamma.core.utils import CONFIG, LOGGER, now, clamp, safe_mean, safe_std, short_hash


class CartographeBrouillage:
    """Cartographie des fragments et zones de tension - version optimisée"""
    
    _MOTS_DIVERGENTS = {"cacher", "secret", "mensonge", "verite cachee", "vérité cachée",
                        "on ne nous dit pas", "revelation", "révélation", "complot",
                        "dissimuler", "occulte", "occulté", "tabou", "censure", "censuré"}
    
    _MOTS_TECHNIQUES = {"quantique", "algorithme", "isotopique", "turing", "cryptographique",
                        "blockchain", "neurale", "spectrographique", "biometrique", "biométrique",
                        "genomique", "génomique"}
    
    _MOTS_EMOTION = {"peur", "colere", "colère", "rage", "panique", "angoisse", "terreur"}
    _MOTS_COGNITIF = {"complexe", "incomprehensible", "incompréhensible", "technique", "jargon"}
    _MOTS_SOCIAL = {"communaute", "communauté", "groupe", "nous vs eux", "divise"}
    _MOTS_INSTITUTION = {"gouvernement", "etat", "état", "autorite", "autorité", "officiel"}
    
    def __init__(self, nom_systeme: str = "Cartographe"):
        self.nom = nom_systeme
        self.fragments: Dict[str, FragmentNarratif] = {}
        self.zones_tension: Dict[str, ZoneDeTension] = {}
        self.sujets_suivis: Set[str] = set()
        self._dedup_index: Set[str] = set()
        self._fragments_par_sujet_cache: Dict[str, List[str]] = {}
    
    def _get_fragments_par_sujet(self, sujet: str) -> List[FragmentNarratif]:
        if sujet not in self._fragments_par_sujet_cache:
            self._fragments_par_sujet_cache[sujet] = [
                fid for fid, f in self.fragments.items() if f.sujet == sujet
            ]
        return [self.fragments[fid] for fid in self._fragments_par_sujet_cache.get(sujet, []) if fid in self.fragments]
    
    def _invalider_cache(self, sujet: str) -> None:
        self._fragments_par_sujet_cache.pop(sujet, None)
    
    def ingerer_fragment(self, sujet: str, type_src: str, contenu: str,
                         charge: float = 3.0, auteur: Optional[str] = None,
                         url: Optional[str] = None) -> Optional[str]:
        if not sujet or not contenu:
            return None
        
        if len(self.fragments) >= CONFIG.max_total_fragments:
            LOGGER.warning("Limite max_total_fragments atteinte")
            return None
        
        if len(self._get_fragments_par_sujet(sujet)) >= CONFIG.max_fragments_par_sujet:
            LOGGER.warning("Limite par sujet atteinte pour %s", sujet)
            return None
        
        contenu = contenu.strip()[:CONFIG.max_len_contenu]
        
        key = f"{sujet}::{short_hash(contenu, 16)}"
        if key in self._dedup_index:
            LOGGER.debug("Fragment dupliqué ignoré: %s", sujet)
            return None
        self._dedup_index.add(key)
        
        charge = clamp(float(charge), 0.0, 10.0)
        type_source = _TYPE_SOURCE_LOOKUP.get(type_src, TypeSource.ARTICLE_PRESSE)
        
        frag_id = f"FRAG_{now().strftime('%Y%m%d%H%M%S%f')}_{short_hash(contenu)}"
        fragment = FragmentNarratif(
            id=frag_id, sujet=sujet, type_source=type_source, contenu=contenu,
            charge_emotionnelle=charge, date_collecte=now(),
            coherence_interne=self._analyser_coherence_interne(contenu),
            divergence_externe=self._analyser_divergence(contenu),
            auteur=auteur, url_source=url
        )
        
        self.fragments[frag_id] = fragment
        self.sujets_suivis.add(sujet)
        self._invalider_cache(sujet)
        LOGGER.debug("Fragment ingéré: %s (%s)", sujet, frag_id[:8])
        return frag_id
    
    def _analyser_coherence_interne(self, contenu: str) -> float:
        c = contenu.lower()
        mots = re.findall(r"\w+", c, flags=re.UNICODE)
        if len(mots) < 15:
            return 0.8
        
        termes_aff = {"est", "sont", "ont", "toujours", "vrai", "certain", "preuve"}
        termes_neg = {"pas", "ne", "ni", "aucun", "jamais", "faux", "douteux"}
        
        pos = sum(1 for m in mots if m in termes_aff)
        neg = sum(1 for m in mots if m in termes_neg)
        
        if pos + neg == 0:
            return 0.7
        return clamp(pos / (pos + neg), 0.3, 1.0)
    
    def _analyser_divergence(self, contenu: str) -> float:
        c = contenu.lower()
        score = sum(0.15 for mot in self._MOTS_DIVERGENTS if mot in c)
        
        if "?" in contenu and any(q in c for q in ("pourquoi", "comment", "qui")):
            score += 0.2
        if any(p in c for p in ("la vérité sur", "la verite sur", "ce qu'on ne vous dit pas")):
            score += 0.3
        
        return clamp(score, 0.0, 1.0)
    
    def _detecter_formes_opacite(self, fragment: FragmentNarratif) -> List[TypeOpacite]:
        opacites = []
        c = fragment.contenu.lower()
        
        nb_tech = sum(1 for t in self._MOTS_TECHNIQUES if t in c)
        if nb_tech >= 1:
            opacites.append(TypeOpacite.COMPLEXITE_TECHNIQUE)
        if nb_tech >= 3:
            opacites.append(TypeOpacite.JARGON_EXCESSIF)
        
        if len(c.split()) > 120 and fragment.type_source == TypeSource.THEORIE_ALTERNATIVE:
            opacites.append(TypeOpacite.SURCHARGE_THEORIQUE)
        
        if fragment.type_source in (TypeSource.MEME, TypeSource.POST_RESEAU_SOCIAL):
            opacites.append(TypeOpacite.PROPAGATION_MEMETIQUE)
        
        if fragment.type_source in (TypeSource.THEORIE_ALTERNATIVE, TypeSource.MEME, TypeSource.POST_RESEAU_SOCIAL):
            if not any(t in c for t in ("selon", "source:", "étude", "etude", "rapport", "d'après", "d'apres")):
                opacites.append(TypeOpacite.ABSENCE_SOURCE)
        
        if (c.count(" je ") + c.count(" mon ") + c.count(" ma ") + c.count(" moi ")) > 3:
            opacites.append(TypeOpacite.ANECDOTISATION)
        
        return opacites
    
    def analyser_sujet(self, sujet: str, recalculer: bool = False) -> Optional[ZoneDeTension]:
        fragments_sujet = self._get_fragments_par_sujet(sujet)
        if not fragments_sujet:
            return None
        
        zone_existante = next((z for z in self.zones_tension.values() if z.sujet == sujet), None)
        
        charges = np.array([f.charge_emotionnelle for f in fragments_sujet])
        divergences = np.array([f.divergence_externe for f in fragments_sujet])
        
        charge_moy = float(np.mean(charges)) if charges.size else 0.0
        divergence_moy = float(np.mean(divergences)) if divergences.size else 0.0
        
        opacites = set()
        for frag in fragments_sujet:
            opacites.update(self._detecter_formes_opacite(frag))
        
        niveau_alerte = self._calculer_niveau_alerte(len(fragments_sujet), charge_moy, divergence_moy, len(opacites))
        energie_estimee = charge_moy * divergence_moy * len(fragments_sujet)
        repartition = self._analyser_repartition_tensions(fragments_sujet)
        resilience = self._calculer_resilience_narrative(fragments_sujet)
        
        if zone_existante and not recalculer:
            zone_existante.resilience_narrative = resilience
            zone_existante.ajouter_point_historique(len(fragments_sujet), resilience)
            return zone_existante
        
        if zone_existante and recalculer:
            zone_existante.fragments_ids = [f.id for f in fragments_sujet]
            zone_existante.niveau_alerte = niveau_alerte
            zone_existante.energie_estimee = energie_estimee
            zone_existante.formes_opacite_detectees = sorted(list(opacites), key=lambda x: x.value)
            zone_existante.ratio_divergences_par_fragment = divergence_moy
            zone_existante.date_derniere_maj = now()
            zone_existante.repartition_tensions = repartition
            zone_existante.resilience_narrative = resilience
            zone_existante.ajouter_point_historique(len(fragments_sujet), resilience)
            return zone_existante
        
        zone_id = f"ZONE_{sujet}_{now().strftime('%Y%m%d%H%M%S%f')}"
        zone = ZoneDeTension(
            id=zone_id, sujet=sujet, fragments_ids=[f.id for f in fragments_sujet],
            niveau_alerte=niveau_alerte, energie_estimee=energie_estimee,
            formes_opacite_detectees=sorted(list(opacites), key=lambda x: x.value),
            ratio_divergences_par_fragment=divergence_moy, date_creation=now(), date_derniere_maj=now(),
            repartition_tensions=repartition, resilience_narrative=resilience
        )
        zone.ajouter_point_historique(len(fragments_sujet), resilience)
        self.zones_tension[zone_id] = zone
        LOGGER.info("Zone créée: %s (alerte: %.1f)", sujet, niveau_alerte)
        return zone
    
    def _calculer_niveau_alerte(self, nb_fragments: int, charge: float, divergence: float, nb_opacites: int) -> float:
        base = (charge * 0.3 + divergence * 10.0 * 0.7) * 0.8
        return clamp(base + min(1.5, nb_fragments * 0.1) + min(2.5, nb_opacites * 0.5), 0.0, 10.0)
    
    def _analyser_repartition_tensions(self, fragments: List[FragmentNarratif]) -> Dict[TypeTension, float]:
        scores = {t: 0.0 for t in TypeTension}
        for frag in fragments:
            c = frag.contenu.lower()
            if any(m in c for m in self._MOTS_EMOTION):
                scores[TypeTension.EMOTIONNELLE] += frag.charge_emotionnelle
            if any(m in c for m in self._MOTS_COGNITIF):
                scores[TypeTension.COGNITIVE] += 1.0
            if any(m in c for m in self._MOTS_SOCIAL):
                scores[TypeTension.SOCIALE] += 1.0
            if any(m in c for m in self._MOTS_INSTITUTION):
                scores[TypeTension.INSTITUTIONNELLE] += 1.0
        
        total = max(len(fragments), 1)
        return {k: clamp(v / total, 0.0, 1.0) for k, v in scores.items()}
    
    def _calculer_resilience_narrative(self, fragments: List[FragmentNarratif]) -> float:
        if len(fragments) < 3:
            return 1.0
        
        fragilite = 0.0
        charges = [f.charge_emotionnelle for f in fragments]
        if safe_mean(charges) > 6.0 and safe_std(charges) < 2.0:
            fragilite += 0.3
        
        div = [f.divergence_externe for f in fragments]
        if safe_std(div) < 0.2:
            fragilite += 0.3
        
        if len(set(f.type_source for f in fragments)) <= 2 and len(fragments) > 5:
            fragilite += 0.2
        
        dates = [f.date_collecte for f in fragments]
        if dates and (max(dates) - min(dates)).days < 7 and len(fragments) > 10:
            fragilite += 0.2
        
        return 1.0 - clamp(fragilite, 0.0, 1.0)
    
    def get_historique_zone(self, zone_id: str) -> List[Dict]:
        zone = self.zones_tension.get(zone_id)
        return [p.to_dict() for p in zone.historique_tension] if zone else []
    
    def analyser_tendance_zone(self, zone_id: str) -> Dict:
        zone = self.zones_tension.get(zone_id)
        if not zone or len(zone.historique_tension) < 2:
            return {"statut": "données_insuffisantes"}
        
        t = zone.tendance_alerte
        if t > 0.3:
            tendance_str = "forte_hausse"
        elif t > 0.1:
            tendance_str = "hausse_modérée"
        elif t < -0.3:
            tendance_str = "forte_baisse"
        elif t < -0.1:
            tendance_str = "baisse_modérée"
        else:
            tendance_str = "stable"
        
        tension_dom = max(zone.repartition_tensions.items(), key=lambda x: x[1])[0] if zone.repartition_tensions else TypeTension.EMOTIONNELLE
        
        return {"tendance": tendance_str, "valeur_tendance": zone.tendance_alerte,
                "volatilite": zone.volatilite, "resilience": zone.resilience_narrative,
                "tension_dominante": tension_dom.value, "points_historique": len(zone.historique_tension)}