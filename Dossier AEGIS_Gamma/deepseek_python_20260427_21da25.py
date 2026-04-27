"""
AEGIS-Γ - Module Contrôleur éthique
"""

import json
from typing import Any, Dict, List

from aegis_gamma.core.enums import ProfilEthique
from aegis_gamma.core.utils import now_iso, clamp


class ControleurEthique:
    """Contrôle éthique des décisions"""

    def __init__(self, profil: ProfilEthique = ProfilEthique.INSTITUTIONNEL):
        self.audits_realises = []
        self.profil = profil
        self.seuils_par_profil = {
            ProfilEthique.CITOYEN: {"score_blocage": 50, "penalite_minimisation": 5, "tolerance_biais": "faible", "transparence": "maximale"},
            ProfilEthique.JOURNALISTIQUE: {"score_blocage": 60, "penalite_minimisation": 10, "tolerance_biais": "moyenne", "transparence": "élevée"},
            ProfilEthique.INSTITUTIONNEL: {"score_blocage": 70, "penalite_minimisation": 15, "tolerance_biais": "forte", "transparence": "modérée"},
            ProfilEthique.RECHERCHE: {"score_blocage": 40, "penalite_minimisation": 20, "tolerance_biais": "critique", "transparence": "maximale"},
        }

    def changer_profil(self, nouveau: ProfilEthique) -> None:
        self.profil = nouveau

    def auditer_decision(self, decision: Dict[str, Any], contexte: Dict[str, Any]) -> Dict[str, Any]:
        seuils = self.seuils_par_profil[self.profil]
        violations = []
        signaux = []
        score = 100

        if not self._decision_explicable(decision):
            impact = -20 if seuils["transparence"] in ("maximale", "élevée") else -10
            violations.append({"principe": "transparence", "severite": "haute",
                              "explication": "Décision insuffisamment expliquée", "impact": impact})

        if not self._reponse_proportionnee(decision, contexte):
            violations.append({"principe": "proportionnalite", "severite": "critique",
                              "explication": "Réponse disproportionnée", "impact": -30})

        biais = self._detecter_biais_culturels(decision)
        if biais:
            if seuils["tolerance_biais"] == "faible":
                violations.append({"principe": "neutralite_culturelle", "severite": "moyenne",
                                  "explication": f"Biais : {', '.join(biais[:2])}", "impact": -15})
            else:
                signaux.append({"type": "avertissement_biais", "details": biais, "impact": -5,
                               "explication": "Biais tolérés selon profil"})

        if self._surcollecte_donnees(decision):
            violations.append({"principe": "minimisation_donnees", "severite": "moyenne",
                              "explication": "Collecte excessive détectée", "impact": -int(seuils["penalite_minimisation"])})

        for v in violations:
            score += v["impact"]
        for s in signaux:
            score += s.get("impact", 0)

        score = int(clamp(score, 0, 100))
        bloque = score < int(seuils["score_blocage"])

        audit = {"date": now_iso(), "score_ethique": score, "profil_utilise": self.profil.value,
                 "seuil_blocage": seuils["score_blocage"], "violations": violations, "signaux": signaux,
                 "recommandations_correctives": self._recommandations(violations, signaux, score),
                 "decision_bloquee": bloque, "explication_publique": self._explication_publique(decision, violations, score, bloque)}
        self.audits_realises.append(audit)
        return audit

    def comparer_profils(self, decision: Dict[str, Any], contexte: Dict[str, Any]) -> Dict[str, Any]:
        profil_orig = self.profil
        comparaison = {}
        for profil in ProfilEthique:
            self.profil = profil
            a = self.auditer_decision(decision, contexte)
            comparaison[profil.value] = {"score": a["score_ethique"], "bloque": a["decision_bloquee"],
                                         "violations": len(a["violations"]), "signaux": len(a.get("signaux", []))}
        self.profil = profil_orig
        non_bloques = [p for p, a in comparaison.items() if not a["bloque"]]
        if non_bloques:
            meilleur = max(non_bloques, key=lambda p: comparaison[p]["score"])
            reco = f"Profil recommandé : {meilleur} (score: {comparaison[meilleur]['score']}/100)"
        else:
            reco = "Aucun profil ne valide cette décision. Révision nécessaire."
        return {"decision": decision.get("sujet", "inconnu"), "comparaison": comparaison, "recommandation_profil": reco}

    def _decision_explicable(self, d: Dict[str, Any]) -> bool:
        return bool(("score_confiance" in d or "validation" in d) and isinstance(d.get("zone_tension"), dict))

    def _reponse_proportionnee(self, d: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
        alerte = float(d.get("zone_tension", {}).get("niveau_alerte", 0.0))
        actions = " ".join(map(str, d.get("prochaines_actions", []) or [])).lower()
        if alerte < 4.0 and ("enquête complète" in actions or "investigation prioritaire" in actions):
            return False
        if alerte >= 8.0 and ("surveillance passive" in actions or "veille occasionnelle" in actions):
            return False
        return True

    def _detecter_biais_culturels(self, d: Dict[str, Any]) -> List[str]:
        contenu = json.dumps(d, ensure_ascii=False).lower()
        return [f"Terme potentiellement biaisé : '{t}'" for t in ["occident", "civilisation", "progrès", "progres", "démocratie", "democratie"] if t in contenu]

    def _surcollecte_donnees(self, d: Dict[str, Any]) -> bool:
        z = d.get("zone_tension", {}) or {}
        return int(z.get("n_fragments", 0)) > 10 and float(z.get("niveau_alerte", 0.0)) < 3.0

    def _recommandations(self, violations: List, signaux: List, score: int) -> List[str]:
        recs = []
        if score < 60:
            recs.append("Suspendre ou revoir la décision avec supervision")
        for v in violations:
            if v.get("principe") == "transparence":
                recs.append("Ajouter une justification détaillée")
            elif v.get("principe") == "proportionnalite":
                recs.append("Réajuster le niveau d'action au niveau d'alerte")
            elif v.get("principe") == "minimisation_donnees":
                recs.append("Réduire la collecte et mettre en place une purge / quotas")
        for s in signaux:
            if s.get("type") == "avertissement_biais":
                recs.append("Revoir le vocabulaire et élargir les références culturelles")
        return recs[:5] if recs else ["Aucune action corrective nécessaire"]

    def _explication_publique(self, d: Dict[str, Any], violations: List, score: int, bloque: bool) -> str:
        sujet = d.get("sujet", "inconnu")
        seuil = int(self.seuils_par_profil[self.profil]["score_blocage"])
        if bloque:
            return f"Décision concernant '{sujet}' suspendue. Score: {score}/100 (seuil: {seuil})."
        if score >= 80:
            return f"Décision concernant '{sujet}' validée éthiquement. Score: {score}/100."
        if violations:
            return f"Décision concernant '{sujet}' validée avec réserves. Score: {score}/100."
        alerte = float(d.get("zone_tension", {}).get("niveau_alerte", 0.0))
        return f"Décision concernant '{sujet}'. Alerte: {alerte:.1f}/10. Score éthique: {score}/100."