"""
AEGIS-Γ - Module Simulateur stratégique
"""

from typing import Any, Dict, List, Optional

import numpy as np

from aegis_gamma.core.models import ZoneDeTension
from aegis_gamma.core.utils import now_iso, clamp, safe_mean


class SimulateurStrategique:
    """Simulation Monte Carlo de stratégies"""

    ACTIONS_REF = {
        "clarification": {"nom": "Publication de clarification", "impact_alerte": -1.5, "impact_resilience": +0.2,
                          "impact_energie": -0.3, "duree_effet": 7, "cout": 2},
        "amplification": {"nom": "Amplification de contre-narratif", "impact_alerte": -2.0, "impact_resilience": +0.3,
                          "impact_energie": -0.5, "duree_effet": 14, "cout": 4},
        "investigation": {"nom": "Investigation approfondie", "impact_alerte": -2.5, "impact_resilience": +0.4,
                          "impact_energie": -0.7, "duree_effet": 30, "cout": 8},
        "desengagement": {"nom": "Désengagement stratégique", "impact_alerte": +0.5, "impact_resilience": -0.1,
                          "impact_energie": -0.8, "duree_effet": 21, "cout": 1},
        "mediation": {"nom": "Médiation avec acteurs clés", "impact_alerte": -1.0, "impact_resilience": +0.5,
                      "impact_energie": -0.4, "duree_effet": 28, "cout": 6},
    }

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)
        self.scenarios_simules = []

    def simuler_scenario(self, zone: ZoneDeTension, actions: List[str],
                         horizon_jours: int = 30, iterations: int = 100) -> Dict[str, Any]:
        actions_valides = [a for a in actions if a in self.ACTIONS_REF]
        if not actions_valides:
            return {"erreur": "Aucune action valide", "actions_invalides": actions}

        scenario_id = f"SCEN_{zone.id[:12]}_{now_iso().replace(':', '-').replace('.', '-')}"
        params_init = {"alerte": zone.niveau_alerte, "energie": zone.energie_estimee,
                       "resilience": zone.resilience_narrative, "volatilite": zone.volatilite}
        impacts = self._impacts_actions(actions_valides)
        sims = [self._run_sim(dict(params_init), impacts, horizon_jours) for _ in range(iterations)]
        agreges = self._agreger(sims)
        eval_ = self._evaluer(agreges, params_init)

        return {"id": scenario_id, "zone": zone.sujet, "zone_id": zone.id, "actions": actions_valides,
                "horizon_jours": horizon_jours, "iterations": iterations, "parametres_initiaux": params_init,
                "impacts_actions": impacts, "resultats_simulation": agreges, "evaluation": eval_,
                "recommandations": self._recommandations(eval_, actions_valides), "date_simulation": now_iso()}

    def comparer_scenarios(self, zone: ZoneDeTension, liste_scenarios: List[List[str]]) -> Dict[str, Any]:
        resultats = []
        for i, actions in enumerate(liste_scenarios):
            s = self.simuler_scenario(zone, actions, horizon_jours=30, iterations=50)
            if "erreur" not in s:
                resultats.append({"scenario_id": f"SCEN_{i+1}", "actions": actions,
                                  "evaluation": s.get("evaluation", {}),
                                  "cout_total": s.get("impacts_actions", {}).get("cout_total", 0)})
        if not resultats:
            return {"erreur": "Aucun scénario valide"}
        resultats.sort(key=lambda x: x.get("evaluation", {}).get("score_global", 0), reverse=True)
        meilleur = resultats[0] if resultats else None
        if meilleur and meilleur["evaluation"].get("efficacite") in ("élevée", "modérée"):
            reco = f"Scénario recommandé : {meilleur['scenario_id']} (score: {meilleur['evaluation'].get('score_global', 0):.2f})"
        else:
            reco = "Aucun scénario satisfaisant — reconsidérer les stratégies"
        return {"zone": zone.sujet, "nombre_scenarios": len(resultats), "comparaison": resultats,
                "recommandation": reco, "meilleur_scenario": meilleur}

    def _impacts_actions(self, actions: List[str]) -> Dict[str, Any]:
        imp = {"impact_alerte": 0.0, "impact_energie": 0.0, "impact_resilience": 0.0,
               "duree_moyenne": 0.0, "cout_total": 0}
        for a in actions:
            ref = self.ACTIONS_REF.get(a, {})
            if ref:
                imp["impact_alerte"] += ref.get("impact_alerte", 0.0)
                imp["impact_energie"] += ref.get("impact_energie", 0.0)
                imp["impact_resilience"] += ref.get("impact_resilience", 0.0)
                imp["duree_moyenne"] = max(imp["duree_moyenne"], ref.get("duree_effet", 0))
                imp["cout_total"] += ref.get("cout", 0)
        return imp

    def _run_sim(self, params: Dict[str, float], impacts: Dict[str, Any], horizon: int) -> Dict[str, List[float]]:
        alerte = [params["alerte"]]
        energie = [params["energie"]]
        resilience = [params["resilience"]]
        vol = params["volatilite"]
        dur = impacts["duree_moyenne"]

        for jour in range(1, horizon + 1):
            mult = max(0.0, 1.0 - (jour / dur)) if dur > 0 else 0.0
            alerte.append(float(clamp(alerte[-1] + impacts["impact_alerte"] * mult + self.rng.normal(0, vol * 0.5), 0, 10)))
            energie.append(float(clamp(energie[-1] + impacts["impact_energie"] * mult + self.rng.normal(0, energie[-1] * 0.1), 0, 100)))
            resilience.append(float(clamp(resilience[-1] + impacts["impact_resilience"] * mult + self.rng.normal(0, 0.05), 0, 1)))
        return {"alerte": alerte, "energie": energie, "resilience": resilience}

    def _agreger(self, sims: List[Dict[str, List[float]]]) -> Dict[str, Any]:
        if not sims:
            return {}
        n = len(sims[0]["alerte"])
        am = np.array([s["alerte"] for s in sims])
        em = np.array([s["energie"] for s in sims])
        rm = np.array([s["resilience"] for s in sims])
        return {
            "moyennes": {"alerte": [float(np.mean(am[:, i])) for i in range(n)],
                         "energie": [float(np.mean(em[:, i])) for i in range(n)],
                         "resilience": [float(np.mean(rm[:, i])) for i in range(n)]},
            "percentiles": {"alerte_5": [float(np.percentile(am[:, i], 5)) for i in range(n)],
                            "alerte_95": [float(np.percentile(am[:, i], 95)) for i in range(n)],
                            "energie_5": [float(np.percentile(em[:, i], 5)) for i in range(n)],
                            "energie_95": [float(np.percentile(em[:, i], 95)) for i in range(n)]},
            "probabilites": {"alerte_baisse_30": float(np.mean([s["alerte"][-1] < s["alerte"][0] * 0.7 for s in sims])),
                             "alerte_baisse_50": float(np.mean([s["alerte"][-1] < s["alerte"][0] * 0.5 for s in sims])),
                             "alerte_hausse_30": float(np.mean([s["alerte"][-1] > s["alerte"][0] * 1.3 for s in sims])),
                             "resilience_amelioration": float(np.mean([s["resilience"][-1] > s["resilience"][0] for s in sims]))}
        }

    def _evaluer(self, res: Dict[str, Any], init: Dict[str, float]) -> Dict[str, Any]:
        if not res or "moyennes" not in res:
            return {"statut": "donnees_insuffisantes"}
        alertes = res["moyennes"].get("alerte", [])
        al_fin = alertes[-1] if alertes else init["alerte"]
        al_init = init["alerte"]
        if al_init == 0:
            return {"efficacite": "neutre", "reduction_absolue": 0, "score_global": 0}
        red = al_init - al_fin
        red_rel = red / al_init
        eff = "élevée" if red_rel >= 0.3 else "modérée" if red_rel >= 0.15 else "faible" if red_rel > 0 else "négative"
        p95 = res.get("percentiles", {}).get("alerte_95", [])
        risque = "élevé" if p95 and p95[-1] > 8 else "modéré" if p95 and p95[-1] > 6 else "faible"
        return {"efficacite": eff, "reduction_absolue": float(red), "reduction_relative": float(red_rel),
                "alerte_finale_moyenne": float(al_fin), "risque": risque,
                "probabilite_succes": float(res.get("probabilites", {}).get("alerte_baisse_30", 0.5)),
                "score_global": float(red_rel * 10 * res.get("probabilites", {}).get("resilience_amelioration", 0.5))}

    def _recommandations(self, eval_: Dict[str, Any], actions: List[str]) -> List[str]:
        recs = []
        eff = eval_.get("efficacite", "")
        risque = eval_.get("risque", "")
        score = eval_.get("score_global", 0)
        if eff == "élevée" and risque == "faible":
            recs.append("Scénario recommandé : bonne efficacité, faible risque")
            if score > 3:
                recs.append("Considérer pour déploiement prioritaire")
        elif eff == "modérée":
            recs.append("Scénario acceptable — efficacité modérée")
            if len(actions) > 2:
                recs.append("Étudier une version simplifiée")
        elif eff in ("faible",) or risque == "élevé":
            recs.append("Scénario à reconsidérer")
            recs.append("Tester des combinaisons alternatives d'actions")
        elif eff == "négative":
            recs.append("Scénario contre-productif : risque d'aggravation")
            recs.append("Revoir les hypothèses de base")
        if "investigation" in actions and "amplification" not in actions:
            recs.append("Ajouter une composante d'amplification pour maximiser l'impact")
        if "desengagement" in actions:
            recs.append("Surveiller étroitement après désengagement (risque de vide)")
        return recs[:5]