"""
AEGIS-Γ - Module Détecteur de coordination
"""

import re
from collections import Counter
from typing import Any, Dict, List
from urllib.parse import urlparse

import numpy as np

from aegis_gamma.core.models import FragmentNarratif
from aegis_gamma.core.utils import timedelta, safe_mean, safe_std, clamp


class DetecteurCoordination:
    """Détection avancée de coordination entre acteurs"""

    def analyser_coordination_avancee(self, fragments: List[FragmentNarratif], fenetre_temps_heures: int = 24) -> Dict[str, Any]:
        if len(fragments) < 10:
            return {"statut": "donnees_insuffisantes", "raison": f"{len(fragments)} fragments (min 10)"}

        tries = sorted(fragments, key=lambda f: f.date_collecte)
        donnees = self._preparer(tries, fenetre_temps_heures)
        analyses = {"temporale": self._coord_temporelle(donnees), "semantique": self._coord_semantique(donnees),
                    "reseau": self._coord_reseau(donnees), "amplification": self._coord_amplification(donnees)}
        campagnes = self._detecter_campagnes(analyses)
        evaluation = self._evaluer(analyses, campagnes)

        return {"statut": "analyse_complete", "nombre_fragments": len(fragments), "analyses_detaillees": analyses,
                "campagnes_detectees": campagnes, "evaluation_globale": evaluation,
                "recommandations": self._recommandations(evaluation, campagnes), "signaux_alertes": self._signaux(evaluation)}

    def _preparer(self, fragments: List[FragmentNarratif], fenetre: int) -> Dict[str, Any]:
        donnees = {"timestamps": [f.date_collecte for f in fragments],
                   "auteurs": [f.auteur or "anonyme" for f in fragments],
                   "contenus": [f.contenu for f in fragments],
                   "charges": [f.charge_emotionnelle for f in fragments],
                   "urls": [f.url_source for f in fragments]}

        if fragments:
            start = fragments[0].date_collecte
            slots = []
            for i in range(fenetre * 2):
                s = start + timedelta(minutes=30 * i)
                e = s + timedelta(minutes=30)
                grp = [f for f in fragments if s <= f.date_collecte < e]
                slots.append({"debut": s, "fin": e, "count": len(grp),
                              "auteurs": list(set(f.auteur or "anonyme" for f in grp)),
                              "charge_moyenne": safe_mean([f.charge_emotionnelle for f in grp])})
            donnees["time_slots"] = slots

        phrases = Counter()
        for c in donnees["contenus"]:
            for ph in re.split(r"[.!?]+", c):
                ph = ph.strip().lower()[:100]
                if len(ph) > 20:
                    phrases[ph] += 1

        hashtags = Counter(ht for c in donnees["contenus"] for ht in re.findall(r"#(\w+)", c))

        donnees["motifs"] = ([{"type": "phrase_repetee", "contenu": ph[:50], "occurrences": cnt,
                               "score_coordination": min(1.0, cnt / 10.0)} for ph, cnt in phrases.items() if cnt >= 3] +
                             [{"type": "hashtag_coordonne", "hashtag": f"#{ht}", "occurrences": cnt,
                               "score_coordination": min(1.0, cnt / 20.0)} for ht, cnt in hashtags.items() if cnt >= 5])
        return donnees

    def _coord_temporelle(self, d: Dict[str, Any]) -> Dict[str, Any]:
        slots = d.get("time_slots", [])
        counts = [s["count"] for s in slots]

        if not counts:
            return {"score_coordination_temporelle": 0.0, "niveau": "faible"}

        moy = safe_mean(counts)
        std = safe_std(counts)
        seuil = moy + 2 * std if std > 0 else moy * 2

        pics = [{"heure": s["debut"].strftime("%H:%M"), "count": c, "intensite": min(1.0, c / max(counts))}
                for s, c in zip(slots, counts) if c > seuil]

        score = min(1.0, len(pics) / max(len([c for c in counts if c > 0]), 1) * 2) if pics else 0.0
        periodicite = self._detecter_periodicite(counts) if len(counts) >= 48 else 0.0
        score = clamp(score * (1.0 + periodicite * 0.3), 0.0, 1.0)

        return {"pics_detectes": pics[:5], "nombre_pics": len(pics), "score_coordination_temporelle": score,
                "periodicite_detectee": periodicite, "niveau": "élevé" if score > 0.7 else "modéré" if score > 0.4 else "faible"}

    def _detecter_periodicite(self, serie: List[int]) -> float:
        if len(serie) < 48:
            return 0.0
        lag = 48
        serie1 = serie[:-lag]
        serie2 = serie[lag:]
        if len(serie1) < 2 or len(serie2) < 2:
            return 0.0
        try:
            correlation = np.corrcoef(serie1, serie2)[0, 1]
            return max(0.0, correlation if not np.isnan(correlation) else 0.0)
        except:
            return 0.0

    def _coord_semantique(self, d: Dict[str, Any]) -> Dict[str, Any]:
        motifs = d.get("motifs", [])
        score = safe_mean([m.get("score_coordination", 0.0) for m in motifs]) if motifs else 0.0
        return {"motifs_detectes": motifs[:10], "nombre_motifs": len(motifs), "score_coordination_semantique": score,
                "niveau": "élevé" if score > 0.6 else "modéré" if score > 0.3 else "faible"}

    def _coord_reseau(self, d: Dict[str, Any]) -> Dict[str, Any]:
        auteurs = d.get("auteurs", [])
        urls = [u for u in d.get("urls", []) if u]
        score = 0.0
        res = {}

        if auteurs:
            cpt = Counter(auteurs)
            freq = {a: c for a, c in cpt.items() if c >= 3}
            if freq:
                vals = sorted(freq.values())
                n = len(vals)
                concentration = 1.0 - sum(p**2 for p in [v / sum(vals) for v in vals])
                concentration = max(0.0, concentration / (1 - 1/n)) if n > 1 else 0.0
                res["analyse_auteurs"] = {"auteurs_actifs": len(freq), "top_auteurs": dict(Counter(freq).most_common(5)),
                                          "concentration_auteurs": concentration}
                score += concentration * 0.6

        if urls:
            doms = [urlparse(u).netloc.replace("www.", "") for u in urls if u]
            if doms:
                cpt_dom = Counter(doms)
                freq_dom = {d: c for d, c in cpt_dom.items() if c >= 2}
                conc_src = len(freq_dom) / max(len(set(doms)), 1)
                res["analyse_sources"] = {"domaines_uniques": len(set(doms)), "top_domaines": dict(Counter(freq_dom).most_common(5)),
                                          "concentration_sources": conc_src}
                score += conc_src * 0.4

        return {**res, "score_coordination_reseau": clamp(score, 0.0, 1.0),
                "niveau": "élevé" if score > 0.7 else "modéré" if score > 0.4 else "faible"}

    def _coord_amplification(self, d: Dict[str, Any]) -> Dict[str, Any]:
        slots = d.get("time_slots", [])
        counts = [s["count"] for s in slots]

        if len(counts) < 10:
            return {"score_amplification": 0.0, "niveau": "faible"}

        seqs = []
        seq_cur = []
        for i in range(1, len(counts)):
            if counts[i] > counts[i - 1] * 1.5:
                if not seq_cur:
                    seq_cur.append(i - 1)
                seq_cur.append(i)
            elif seq_cur:
                if len(seq_cur) >= 3:
                    seqs.append({"debut": slots[seq_cur[0]]["debut"].strftime("%H:%M"),
                                 "fin": slots[seq_cur[-1]]["debut"].strftime("%H:%M"),
                                 "duree_slots": len(seq_cur), "croissance": counts[seq_cur[-1]] / max(1, counts[seq_cur[0]])})
                seq_cur = []

        score = 0.0
        if seqs:
            moy_croiss = safe_mean([s["croissance"] for s in seqs])
            score = min(1.0, len(seqs) * 0.2 + moy_croiss * 0.3)

        return {"sequences_amplification": seqs[:3], "nombre_sequences": len(seqs), "score_amplification": score,
                "niveau": "élevé" if score > 0.6 else "modéré" if score > 0.3 else "faible"}

    def _detecter_campagnes(self, analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        scores = [analyses["temporale"].get("score_coordination_temporelle", 0.0),
                  analyses["semantique"].get("score_coordination_semantique", 0.0),
                  analyses["reseau"].get("score_coordination_reseau", 0.0),
                  analyses["amplification"].get("score_amplification", 0.0)]
        sc = safe_mean([s for s in scores if s > 0])
        if sc <= 0.5:
            return []

        fp = [k for k, s in zip(["temporale", "semantique", "reseau", "amplification"], scores) if s > 0.6]
        niv = ("hautement_organisée" if sc > 0.8 and len(fp) >= 3 else
               "organisée" if sc > 0.6 and len(fp) >= 2 else
               "semi-organisée" if sc > 0.4 else "émergente")

        return [{"score_composite": sc, "niveau_confiance": min(1.0, sc * 1.2),
                 "force_points": fp, "estimation_organisation": niv}]

    def _evaluer(self, analyses: Dict[str, Any], campagnes: List) -> Dict[str, Any]:
        scores = [analyses["temporale"].get("score_coordination_temporelle", 0.0),
                  analyses["semantique"].get("score_coordination_semantique", 0.0),
                  analyses["reseau"].get("score_coordination_reseau", 0.0),
                  analyses["amplification"].get("score_amplification", 0.0)]
        sg = safe_mean(scores)
        return {"score_global": sg, "niveau_coordination": "élevé" if sg > 0.7 else "modéré" if sg > 0.4 else "faible",
                "campagnes_detectees": len(campagnes) > 0, "nombre_campagnes": len(campagnes),
                "risque_manipulation": "élevé" if sg > 0.7 else "modéré" if sg > 0.5 else "faible",
                "recommandation_priorite": "haute" if sg > 0.7 else "moyenne" if sg > 0.5 else "basse"}

    def _recommandations(self, eval_: Dict, campagnes: List) -> List[str]:
        recs = []
        niveau = eval_.get("niveau_coordination", "")
        if niveau == "élevé":
            recs += ["Investigation prioritaire : forte suspicion de coordination",
                     "Cartographier les acteurs et leurs interconnections",
                     "Surveiller en temps réel les canaux d'amplification"]
        if campagnes:
            recs.append(f"Suivre spécifiquement {len(campagnes)} campagne(s) détectée(s)")
        if niveau == "modéré":
            recs += ["Surveillance renforcée", "Documenter les patterns pour analyse future"]
        if not recs:
            recs.append("Surveillance normale : faible coordination détectée")
        return recs[:6]

    def _signaux(self, eval_: Dict) -> List[Dict[str, Any]]:
        sg = eval_.get("score_global", 0.0)
        camps = eval_.get("campagnes_detectees", False)
        if sg > 0.8:
            return [{"type": "alerte_critique", "niveau": "critique",
                     "message": "Coordination extrêmement élevée — intervention urgente",
                     "actions_recommandees": ["Alerter direction", "Activer protocole crise", "Documenter"]}]
        if sg > 0.6 and camps:
            return [{"type": "alerte_haute", "niveau": "haute",
                     "message": "Campagne coordonnée détectée",
                     "actions_recommandees": ["Investigation approfondie", "Surveillance rapprochée"]}]
        if eval_.get("risque_manipulation") == "modéré":
            return [{"type": "alerte_moderee", "niveau": "modérée",
                     "message": "Signaux de coordination modérée",
                     "actions_recommandees": ["Renforcer monitoring", "Préparer briefing"]}]
        return []