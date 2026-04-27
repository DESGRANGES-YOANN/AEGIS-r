"""
AEGIS-Γ - Module Validateur terrain
"""

from typing import Any, Dict, List, Optional

from aegis_gamma.core.models import ZoneDeTension
from aegis_gamma.core.utils import LOGGER, now_iso, safe_mean
from aegis_gamma.modules.cartographe import CartographeBrouillage


class ValidateurTerrain:
    """Validation des hypothèses sur le terrain"""

    def __init__(self, cartographe: CartographeBrouillage):
        self.cartographe = cartographe
        self.tests_realises: List[Dict[str, Any]] = []
        self.taux_succes = 0.0
        self.version_regles = "4.0.0"

    def tester_hypothese_nulle(self, zone: ZoneDeTension, params: Optional[Dict] = None) -> Dict[str, Any]:
        params = params or {"seuil_coherence": 0.6, "seuil_diversite": 3, "seuil_charge": 5.0,
                           "seuil_opacites": 2, "seuil_anomalies": 3}

        frags = [self.cartographe.fragments.get(fid) for fid in zone.fragments_ids]
        frags = [f for f in frags if f]

        if not frags:
            return {"tests": [], "anomalies_detectees": 0, "hypothese_nulle_rejetee": False,
                    "confiance_validation": 0.0, "erreur": "Aucun fragment disponible",
                    "parametres_utilises": params, "version_regles": self.version_regles}

        tests = [
            {"nom": "Cohérence interne", "resultat": "FAIBLE" if safe_mean([f.coherence_interne for f in frags]) < params["seuil_coherence"] else "ÉLEVÉE",
             "valeur": safe_mean([f.coherence_interne for f in frags]), "seuil": params["seuil_coherence"],
             "explication": "Faible cohérence peut indiquer confusion ou bruit"},
            {"nom": "Diversité des sources", "resultat": "ÉLEVÉE" if len(set(f.type_source for f in frags)) >= params["seuil_diversite"] else "FAIBLE",
             "valeur": len(set(f.type_source for f in frags)), "seuil": params["seuil_diversite"],
             "explication": "Multiples types de sources amplifient la diffusion"},
            {"nom": "Charge émotionnelle", "resultat": "ÉLEVÉE" if safe_mean([f.charge_emotionnelle for f in frags]) >= params["seuil_charge"] else "FAIBLE",
             "valeur": safe_mean([f.charge_emotionnelle for f in frags]), "seuil": params["seuil_charge"],
             "explication": "Émotion élevée favorise la viralité"},
            {"nom": "Techniques d'opacité", "resultat": "ÉLEVÉE" if len(zone.formes_opacite_detectees) >= params["seuil_opacites"] else "FAIBLE",
             "valeur": len(zone.formes_opacite_detectees), "seuil": params["seuil_opacites"],
             "explication": "Plusieurs techniques d'opacité augmentent le risque de confusion"}
        ]

        anomalies = sum(1 for t in tests if t["resultat"] == "ÉLEVÉE")
        rejetee = anomalies >= params["seuil_anomalies"]
        confiance = (anomalies / len(tests)) * 100 if tests else 0.0

        self.tests_realises.append({"date": now_iso(), "zone": zone.id, "anomalies": anomalies,
                                    "confiance": confiance, "parametres": params})

        if len(self.tests_realises) >= 10:
            self._recalculer_taux_succes()

        return {"tests": tests, "anomalies_detectees": anomalies, "hypothese_nulle_rejetee": rejetee,
                "confiance_validation": confiance, "recommandation": self._recommandation(anomalies, rejetee),
                "parametres_utilises": params, "version_regles": self.version_regles}

    def _recommandation(self, anomalies: int, rejetee: bool) -> str:
        if not rejetee:
            return "Considérer comme bruit informationnel normal. Surveiller passivement."
        if anomalies >= 4:
            return "Investigation prioritaire : suspicion élevée de brouillage."
        if anomalies >= 3:
            return "Investigation recommandée : signaux significatifs."
        return "Surveillance accrue : signaux partiels."

    def _recalculer_taux_succes(self) -> None:
        last = self.tests_realises[-10:]
        rejets = sum(1 for t in last if t.get("anomalies", 0) >= 3 and t.get("confiance", 0) >= 60)
        self.taux_succes = rejets / 10.0

    def simuler_validation(self, zone: ZoneDeTension) -> Dict[str, Any]:
        sims = [
            {"nom": "Seuils stricts", "seuil_anomalies": 4, "seuil_charge": 6.0},
            {"nom": "Seuils moyens", "seuil_anomalies": 3, "seuil_charge": 5.0},
            {"nom": "Seuils larges", "seuil_anomalies": 2, "seuil_charge": 4.0},
        ]
        resultats = []
        for sim in sims:
            p = {"seuil_coherence": 0.6, "seuil_diversite": 3, "seuil_charge": sim["seuil_charge"],
                 "seuil_opacites": 2, "seuil_anomalies": sim["seuil_anomalies"]}
            r = self.tester_hypothese_nulle(zone, p)
            resultats.append({"scenario": sim["nom"], "hypothese_rejetee": r["hypothese_nulle_rejetee"],
                              "anomalies": r["anomalies_detectees"], "confiance": r["confiance_validation"],
                              "parametres": p})
        return {"zone": zone.sujet, "simulations": resultats,
                "recommandation_scenario": self._choisir_scenario(resultats)}

    def _choisir_scenario(self, sims: List[Dict[str, Any]]) -> str:
        if not sims:
            return "Aucune simulation disponible"
        best = max(sims, key=lambda s: s["anomalies"] * (s["confiance"] / 100.0))
        score = best["anomalies"] * (best["confiance"] / 100.0)
        return f"Scénario recommandé : {best['scenario']} (score: {score:.2f})"