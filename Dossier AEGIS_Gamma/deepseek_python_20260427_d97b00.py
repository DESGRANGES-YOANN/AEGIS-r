"""
AEGIS-Γ - Module Interface système expert
"""

from typing import Any, Dict, List, Optional

from aegis_gamma.core.enums import TypeSource
from aegis_gamma.core.models import FragmentNarratif
from aegis_gamma.core.utils import now_iso, safe_mean, clamp


class InterfaceSystemeExpert:
    """Interface de système expert pour explications"""

    BASE_CONNAISSANCES = [
        {"id": "KB001", "categorie": "detection_brouillage",
         "connaissance": "Une concentration élevée de termes techniques peut indiquer une tentative d'opacification",
         "confiance": 0.8},
        {"id": "KB002", "categorie": "detection_brouillage",
         "connaissance": "La répétition de phrases identiques par différents auteurs suggère une coordination",
         "confiance": 0.9},
        {"id": "KB003", "categorie": "evaluation_risque",
         "connaissance": "Charge émotionnelle > 7/10 avec faible cohérence interne indique un risque élevé de viralité",
         "confiance": 0.75},
        {"id": "KB004", "categorie": "strategie_reponse",
         "connaissance": "Pour les récits à faible résilience, les clarifications précoces sont plus efficaces",
         "confiance": 0.85},
        {"id": "KB005", "categorie": "analyse_reseau",
         "connaissance": "Un réseau avec peu de nœuds centraux mais fortement connectés est vulnérable à la désinformation",
         "confiance": 0.7},
    ]

    REGLES_EXPERTES = [
        {"id": "R001", "conditions": [{"var": "niveau_alerte", "op": ">=", "val": 8.0},
                                      {"var": "charge_emotionnelle_moyenne", "op": ">=", "val": 7.0}],
         "conclusion": "risque_critique", "explication": "Niveau d'alerte très élevé combiné à une charge émotionnelle forte",
         "confiance": 0.9, "actions": ["alerte_immediate", "mobilisation_equipe"]},
        {"id": "R002", "conditions": [{"var": "coherence_interne_moyenne", "op": "<", "val": 0.4},
                                      {"var": "divergence_externe_moyenne", "op": ">", "val": 0.7}],
         "conclusion": "brouillage_probable", "explication": "Faible cohérence interne avec forte divergence externe suggère une manipulation",
         "confiance": 0.8, "actions": ["investigation_approfondie", "verification_sources"]},
        {"id": "R003", "conditions": [{"var": "resilience_narrative", "op": "<", "val": 0.3},
                                      {"var": "volatilite", "op": ">", "val": 0.4}],
         "conclusion": "fragilite_extreme", "explication": "Récit extrêmement fragile avec haute volatilité",
         "confiance": 0.85, "actions": ["renforcement_resilience", "surveillance_rapprochee"]},
        {"id": "R004", "conditions": [{"var": "nombre_formes_opacite", "op": ">=", "val": 4},
                                      {"var": "diversite_sources", "op": "<", "val": 0.3}],
         "conclusion": "campagne_coordonnee", "explication": "Multiples techniques d'opacité avec sources limitées",
         "confiance": 0.75, "actions": ["analyse_coordination", "cartographie_acteurs"]},
    ]

    def __init__(self):
        self.historique_explications = []

    def generer_explication_decision(self, decision: Dict[str, Any], contexte: Dict[str, Any],
                                     fragments: Optional[List[FragmentNarratif]] = None) -> Dict[str, Any]:
        variables = self._construire_variables(decision, fragments)
        facteurs = self._facteurs(decision, contexte)
        conclusions = self._appliquer_regles(variables)
        connaissances = self._connaissances_pertinentes(decision)
        narrative = self._narrative(facteurs, conclusions, connaissances)
        confiance = self._confiance(facteurs, conclusions)

        return {"decision_id": decision.get("decision_id") or decision.get("id", "inconnu"),
                "sujet": decision.get("sujet", "inconnu"), "date_generation": now_iso(),
                "explication_narrative": narrative, "facteurs_cles": facteurs, "conclusions_expertes": conclusions,
                "connaissances_pertinentes": connaissances, "niveau_confiance_explication": confiance,
                "recommandations_explicatives": self._reco_expl(conclusions)}

    def _construire_variables(self, decision: Dict[str, Any], fragments: Optional[List[FragmentNarratif]]) -> Dict[str, float]:
        zone = decision.get("zone_tension", {}) or {}
        if fragments:
            charge_moy = safe_mean([f.charge_emotionnelle for f in fragments])
            coherence_moy = safe_mean([f.coherence_interne for f in fragments])
            divergence_moy = safe_mean([f.divergence_externe for f in fragments])
            diversite = len(set(f.type_source for f in fragments)) / len(TypeSource)
        else:
            charge_moy = float(zone.get("charge_emotionnelle_moyenne", 0.0))
            coherence_moy = float(zone.get("coherence_interne_moyenne", 0.5))
            divergence_moy = float(zone.get("ratio_divergence", 0.5))
            diversite = float(zone.get("diversite_sources", 0.3))
        return {"niveau_alerte": float(zone.get("niveau_alerte", 0.0)), "charge_emotionnelle_moyenne": charge_moy,
                "coherence_interne_moyenne": coherence_moy, "divergence_externe_moyenne": divergence_moy,
                "resilience_narrative": float(zone.get("resilience_narrative", 1.0)), "volatilite": float(zone.get("volatilite", 0.0)),
                "nombre_formes_opacite": float(len(zone.get("formes_opacite", []))), "diversite_sources": diversite}

    def _appliquer_regles(self, variables: Dict[str, float]) -> List[Dict[str, Any]]:
        conclusions = []
        OPS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b,
               "<": lambda a, b: a < b, "==": lambda a, b: abs(a - b) < 0.001}
        for regle in self.REGLES_EXPERTES:
            if all(OPS[c["op"]](variables.get(c["var"], 0.0), c["val"]) for c in regle["conditions"]):
                conclusions.append({"regle_id": regle["id"], "conclusion": regle["conclusion"],
                                    "explication": regle["explication"], "confiance": regle["confiance"],
                                    "actions_recommandees": regle.get("actions", []),
                                    "variables_evaluees": {c["var"]: variables.get(c["var"], 0.0) for c in regle["conditions"]}})
        return conclusions

    def _facteurs(self, decision: Dict[str, Any], contexte: Dict[str, Any]) -> List[Dict[str, Any]]:
        zone = decision.get("zone_tension", {}) or {}
        validation = decision.get("validation", {}) or {}
        alerte = float(zone.get("niveau_alerte", 0.0))
        poids_a = ("très_fort" if alerte >= 7 else "fort" if alerte >= 5 else "modéré" if alerte >= 3 else "faible")
        conf_val = float(validation.get("confiance_validation", 0.0))
        hyp_rej = validation.get("hypothese_nulle_rejetee", False)
        resilience = float(zone.get("resilience_narrative", 1.0))
        tendance = contexte.get("analyse_tendance", {}).get("tendance", "stable")
        return [{"facteur": "niveau_alerte", "valeur": alerte, "poids": poids_a, "explication": f"Niveau d'alerte de {alerte:.1f}/10"},
                {"facteur": "validation_hypothese", "valeur": "rejetée" if hyp_rej else "non_rejetée",
                 "poids": "fort" if hyp_rej else "modéré",
                 "explication": f"Hypothèse {'rejetée' if hyp_rej else 'non rejetée'} ({conf_val:.0f}%)"},
                {"facteur": "resilience_narrative", "valeur": resilience, "poids": "modéré" if resilience < 0.5 else "faible",
                 "explication": f"Résilience à {resilience:.2f}"},
                {"facteur": "tendance", "valeur": tendance, "poids": "fort" if tendance in ("forte_hausse", "forte_baisse") else "modéré",
                 "explication": f"Tendance : {tendance}"}]

    def _connaissances_pertinentes(self, decision: Dict[str, Any]) -> List[Dict[str, Any]]:
        zone = decision.get("zone_tension", {}) or {}
        criteres = []
        if float(zone.get("niveau_alerte", 0.0)) >= 7:
            criteres += ["detection_brouillage", "evaluation_risque"]
        if len(zone.get("formes_opacite", [])) >= 3:
            criteres.append("detection_brouillage")
        if float(zone.get("resilience_narrative", 1.0)) < 0.5:
            criteres.append("strategie_reponse")
        pertinentes = [c for c in self.BASE_CONNAISSANCES if c["categorie"] in criteres]
        pertinentes.sort(key=lambda c: c["confiance"], reverse=True)
        return pertinentes[:3]

    def _narrative(self, facteurs: List, conclusions: List, connaissances: List) -> str:
        txt = "Cette décision repose sur plusieurs éléments d'analyse :\n\n"
        forts = [f for f in facteurs if f.get("poids") in ("très_fort", "fort")]
        if forts:
            txt += "• Facteurs déterminants :\n" + "".join(f"  - {f['explication']}\n" for f in forts[:2]) + "\n"
        if conclusions:
            txt += "• Évaluations expertes :\n" + "".join(f"  - {c['explication']} (confiance: {c['confiance']:.0%})\n" for c in conclusions[:2]) + "\n"
        if connaissances:
            txt += "• Connaissances applicables :\n" + "".join(f"  - {c['connaissance'][:100]}...\n" for c in connaissances[:2])
        txt += "\nCes éléments combinés justifient la décision prise." if (forts or conclusions) else \
               "\nL'analyse n'a pas identifié de signaux forts — décision prudente."
        return txt

    def _confiance(self, facteurs: List, conclusions: List) -> float:
        score = sum({"très_fort": 0.3, "fort": 0.2, "modéré": 0.1}.get(f.get("poids", ""), 0) for f in facteurs)
        if conclusions:
            score += min(0.4, len(conclusions) * 0.15)
        return float(clamp(score, 0.0, 1.0))

    def _reco_expl(self, conclusions: List) -> List[str]:
        recs = []
        if not conclusions:
            recs.append("Enrichir la base de règles expertes pour ce type de décision")
        if len(conclusions) > 3:
            recs.append("Prioriser les 2-3 conclusions les plus pertinentes")
        recs.append("Préparer une version simplifiée pour les parties prenantes non techniques")
        return recs

    def questionner_systeme(self, question: str, contexte: Optional[Dict[str, Any]] = None,
                            fragments: Optional[List[FragmentNarratif]] = None) -> Dict[str, Any]:
        ql = question.lower()
        if any(m in ql for m in ("pourquoi", "raison", "justification")):
            tq = "explication_decision"
        elif any(m in ql for m in ("comment", "fonctionne", "méthode")):
            tq = "explication_processus"
        elif any(m in ql for m in ("risque", "danger", "problème")):
            tq = "evaluation_risque"
        elif any(m in ql for m in ("solution", "recommandation", "conseil")):
            tq = "recommandation"
        else:
            tq = "general"
        if tq == "explication_decision" and contexte:
            reponse = self.generer_explication_decision(contexte, {}, fragments)
        else:
            generiques = {"explication_processus": {"contenu": "Le système analyse les fragments selon cohérence, divergence, charge émotionnelle et patterns d'opacité."},
                          "evaluation_risque": {"contenu": "Les risques sont évalués sur 0-10. Score >7 : risque élevé. 4-7 : surveillance. <4 : bruit normal."},
                          "recommandation": {"contenu": "Haut risque : investigation. Risque modéré : surveillance active. Faible : veille passive."},
                          "general": {"contenu": "Système expert d'analyse des narratives détectant les patterns de brouillage informationnel."}}
            reponse = generiques.get(tq, generiques["general"])
        return {"question": question, "type_question": tq, "reponse": reponse, "date_reponse": now_iso()}