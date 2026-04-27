"""
AEGIS-Γ - Module Analyseur de crédibilité (Module 16)
Version: 4.0.0
"""

import re
import asyncio
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from aegis_gamma.core.enums import TypeSource, TypeSourceCredibilite
from aegis_gamma.core.models import FragmentNarratif
from aegis_gamma.core.utils import CONFIG, LOGGER, now, now_iso, clamp


class GestionnaireBiaisCredibilite:
    def __init__(self):
        self.biais_connus = [
            {"type": "sous_representation_geographique", "impact": 0.25,
             "raison": "Sources non-occidentales sous-représentées dans les références"},
            {"type": "favoritisme_institutionnel", "impact": 0.15,
             "raison": "Les sources officielles reçoivent un score plus élevé"}]
    
    def evaluer_biais_potentiel(self, fragment: FragmentNarratif) -> Dict:
        biais_detectes = []
        if fragment.pays and fragment.pays not in ["France", "Canada", "Belgique", "Suisse", "USA", "UK"]:
            biais_detectes.append({"type": "sous_representation_geographique", "severite": "moderee",
                                   "explication": f"Provenance: {fragment.pays}", "impact_estime": 0.15})
        if fragment.langue != "fr":
            biais_detectes.append({"type": "anciennete_linguistique", "severite": "elevee" if fragment.langue not in ["en", "es"] else "moderee",
                                   "explication": f"Langue: {fragment.langue}", "impact_estime": 0.25 if fragment.langue not in ["en", "es"] else 0.10})
        return {"biais_detectes": biais_detectes, "confiance_impactee": len(biais_detectes) > 0,
                "recommandation": "⚠️ Biais potentiel significatif" if any(b["severite"] == "elevee" for b in biais_detectes) else "Biais modérés"}


class AnalyseurCredibilite:
    """Analyseur de crédibilité - Version complète"""
    
    SCORES_BASE = {TypeSourceCredibilite.OFFICIEL_VERIFIE: 0.85, TypeSourceCredibilite.ACADEMIQUE: 0.85,
                   TypeSourceCredibilite.PRESSE_RECOMMANDEE: 0.80, TypeSourceCredibilite.OFFICIEL_NON_VERIFIE: 0.65,
                   TypeSourceCredibilite.PRESSE_AUTRE: 0.55, TypeSourceCredibilite.RESEAU_SOCIAL_VERIFIE: 0.50,
                   TypeSourceCredibilite.BLOG_PERSONNEL: 0.40, TypeSourceCredibilite.RESEAU_SOCIAL_ANONYME: 0.30,
                   TypeSourceCredibilite.INCONNU: 0.35}
    
    def __init__(self, seed: Optional[int] = None, use_semantic: bool = True):
        self.use_semantic = use_semantic
        self.historique = []
        self.scores_domaines = {}
        self.scores_auteurs = {}
        self.gestionnaire_biais = GestionnaireBiaisCredibilite()
        self.domaines_recommandes = {"lemonde.fr", "liberation.fr", "reuters.com", "bbc.com", "nytimes.com", "science.org", "nature.com"}
        self.domaines_officiels = {"gouv.fr", "who.int", "un.org", "europa.eu", "insee.fr"}
        if use_semantic:
            LOGGER.info("✅ Mode sémantique activé pour crédibilité")
    
    async def analyser_credibilite_async(self, fragment: FragmentNarratif) -> Dict:
        evaluation_biais = self.gestionnaire_biais.evaluer_biais_potentiel(fragment)
        credibilite_source = self._evaluer_source(fragment)
        credibilite_contenu = await self._evaluer_contenu_async(fragment)
        score_composite = self._score_composite(credibilite_source, credibilite_contenu)
        anomalies = self._detecter_anomalies(fragment, score_composite)
        recommandations = self._recommandations(anomalies, score_composite)
        return {"fragment_id": fragment.id, "sujet": fragment.sujet, "date_analyse": now_iso(),
                "credibilite_source": credibilite_source, "credibilite_contenu": credibilite_contenu,
                "score_credibilite_global": score_composite, "niveau_credibilite": self._niveau(score_composite),
                "anomalies_detectees": anomalies, "recommandations": recommandations, "biais_identifies": evaluation_biais}
    
    def _evaluer_source(self, fragment: FragmentNarratif) -> Dict:
        type_cred = self._categoriser_source(fragment)
        score_base = self.SCORES_BASE.get(type_cred, 0.5)
        ajustements = []
        if fragment.url_source:
            domaine = self._extraire_domaine(fragment.url_source)
            score_domaine = self.scores_domaines.get(domaine, score_base)
            ajustements.append(("domaine", (score_domaine - score_base) * 0.5))
        if fragment.auteur:
            score_auteur = self.scores_auteurs.get(fragment.auteur, score_base)
            ajustements.append(("auteur", (score_auteur - score_base) * 0.5))
        jours_age = (now() - fragment.date_collecte).days
        ajustement_age = max(-0.2, -0.01 * jours_age) if jours_age > 30 else 0.0
        if ajustement_age != 0:
            ajustements.append(("anciennete", ajustement_age))
        score_final = clamp(score_base + sum(a[1] for a in ajustements), 0.0, 1.0)
        return {"type_source": fragment.type_source.value, "categorie_credibilite": type_cred.value,
                "score_base": round(score_base, 3), "ajustements": {a[0]: round(a[1], 3) for a in ajustements},
                "score_source": round(score_final, 3)}
    
    def _categoriser_source(self, fragment: FragmentNarratif) -> TypeSourceCredibilite:
        mapping = {TypeSource.RAPPORT_OFFICIEL: TypeSourceCredibilite.OFFICIEL_VERIFIE,
                   TypeSource.RAPPORT_TECHNIQUE: TypeSourceCredibilite.OFFICIEL_NON_VERIFIE,
                   TypeSource.ARTICLE_PRESSE: TypeSourceCredibilite.PRESSE_AUTRE,
                   TypeSource.TEMOIGNAGE: TypeSourceCredibilite.RESEAU_SOCIAL_VERIFIE,
                   TypeSource.DOCUMENT_HISTORIQUE: TypeSourceCredibilite.ACADEMIQUE,
                   TypeSource.THEORIE_ALTERNATIVE: TypeSourceCredibilite.BLOG_PERSONNEL,
                   TypeSource.MEME: TypeSourceCredibilite.RESEAU_SOCIAL_ANONYME,
                   TypeSource.POST_RESEAU_SOCIAL: TypeSourceCredibilite.RESEAU_SOCIAL_ANONYME,
                   TypeSource.OEUVRE_FICTION: TypeSourceCredibilite.BLOG_PERSONNEL}
        base = mapping.get(fragment.type_source, TypeSourceCredibilite.INCONNU)
        if fragment.url_source:
            domaine = self._extraire_domaine(fragment.url_source)
            if domaine in self.domaines_recommandes:
                return TypeSourceCredibilite.PRESSE_RECOMMANDEE
            if domaine in self.domaines_officiels:
                return TypeSourceCredibilite.OFFICIEL_VERIFIE
        return base
    
    async def _evaluer_contenu_async(self, fragment: FragmentNarratif) -> Dict:
        score_linguistique = self._evaluer_linguistique(fragment)
        score_final = score_linguistique
        return {"score_contenu": round(score_final, 3), "methode": "linguistique",
                "detail_linguistique": round(score_linguistique, 3)}
    
    def _evaluer_linguistique(self, fragment: FragmentNarratif) -> float:
        contenu = fragment.contenu.lower()
        faibles = ["source anonyme", "on dit que", "paraît-il", "rumeur", "selon certaines sources"]
        penalite = min(0.3, sum(0.05 for ind in faibles if ind in contenu))
        forts = ["selon l'étude", "données vérifiées", "consensus scientifique", "méta-analyse"]
        bonus = min(0.2, sum(0.05 for ind in forts if ind in contenu))
        a_sources = bool(re.search(r'https?://[^\s]+', contenu) or "selon" in contenu)
        a_chiffres = bool(re.search(r'\d+(?:[.,]\d+)?\s?(?:%|€|\$|millions?)', contenu))
        score = 0.6 - penalite + bonus + (0.1 if a_sources else -0.05) + (0.05 if a_chiffres else 0.0)
        return clamp(score, 0.0, 1.0)
    
    def _score_composite(self, cred_source: Dict, cred_contenu: Dict) -> float:
        score = cred_source["score_source"] * 0.45 + cred_contenu["score_contenu"] * 0.55
        return round(clamp(score, 0.0, 1.0), 3)
    
    def _niveau(self, score: float) -> str:
        if score >= 0.8:
            return "très_élevée"
        if score >= 0.6:
            return "élevée"
        if score >= 0.4:
            return "modérée"
        if score >= 0.2:
            return "faible"
        return "très_faible"
    
    def _detecter_anomalies(self, fragment: FragmentNarratif, score: float) -> List[Dict]:
        anomalies = []
        if score < 0.3 and fragment.type_source in (TypeSource.RAPPORT_OFFICIEL, TypeSource.RAPPORT_TECHNIQUE):
            anomalies.append({"type": "incoherence_source_contenu", "severite": "haute",
                              "description": "Source officielle avec contenu de très faible crédibilité",
                              "recommandation": "Vérifier l'authenticité du document"})
        if fragment.divergence_externe > 0.7 and score < 0.4:
            anomalies.append({"type": "divergence_anormale", "severite": "haute",
                              "description": f"Forte divergence ({fragment.divergence_externe:.2f}) pour crédibilité faible",
                              "recommandation": "Rechercher des sources contradictoires"})
        if fragment.charge_emotionnelle > 8.0 and score < 0.5:
            anomalies.append({"type": "emotion_excessive", "severite": "haute",
                              "description": f"Charge émotionnelle très élevée ({fragment.charge_emotionnelle}/10)",
                              "recommandation": "Suspecter une manipulation émotionnelle"})
        return anomalies
    
    def _recommandations(self, anomalies: List[Dict], score: float) -> List[str]:
        recs = []
        if score < 0.3:
            recs.append("⚠️ Fragment non fiable - ne pas utiliser comme source")
            recs.append("Rechercher des sources alternatives vérifiées")
        elif score < 0.5:
            recs.append("⚠️ Crédibilité faible - vérifier avant utilisation")
            recs.append("Croiser avec au moins 2 autres sources")
        elif score < 0.7:
            recs.append("Crédibilité modérée - utilisable avec précaution")
        else:
            recs.append("Source fiable - peut être utilisée")
        for a in anomalies:
            if a.get("severite") == "haute":
                recs.append(a["recommandation"])
        return recs[:4]
    
    def _extraire_domaine(self, url: str) -> str:
        try:
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return ""
    
    def analyser_credibilite(self, fragment: FragmentNarratif) -> Dict:
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.analyser_credibilite_async(fragment))
                return future.result(timeout=30)
        except RuntimeError:
            return asyncio.run(self.analyser_credibilite_async(fragment))