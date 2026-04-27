"""
AEGIS-Γ - Module Prédicteur temporel
"""

import datetime as dt
from typing import Any, Dict, List

import numpy as np

from aegis_gamma.core.models import PointTension, ZoneDeTension
from aegis_gamma.core.utils import CONFIG, clamp, safe_mean, timedelta


class PredicteurTemporel:
    """Prédiction de l'évolution des tensions narratives (horizon ≤ 7 jours)"""

    HORIZON_MAX = 7

    def __init__(self, horizon_jours: int = 7):
        self.horizon = min(horizon_jours, self.HORIZON_MAX)
        self.predictions_cache: Dict[str, List[Dict[str, Any]]] = {}

    def predire_evolution_zone(self, zone: ZoneDeTension, points_historique: List[PointTension]) -> Dict[str, Any]:
        if len(points_historique) < 5:
            return {"erreur": f"Données insuffisantes ({len(points_historique)} points, minimum 5)"}

        points_tries = sorted(points_historique, key=lambda p: p.date)
        points_recents = points_tries[-30:]
        alertes = [p.niveau_alerte for p in points_recents]
        energies = [p.energie_estimee for p in points_recents]
        dates = [p.date for p in points_recents]

        if len(alertes) < 2:
            return {"erreur": "Pas assez de points pour la prédiction"}

        x = np.arange(len(alertes))
        coeff_alerte = np.polyfit(x, alertes, 1)
        coeff_energie = np.polyfit(x, energies, 1)

        predictions = []
        for i in range(1, self.horizon + 1):
            future_x = len(alertes) + i
            pred_alerte = coeff_alerte[0] * future_x + coeff_alerte[1]
            pred_energie = coeff_energie[0] * future_x + coeff_energie[1]
            ajust = self._ajustement_hebdo(i, dates, alertes)
            predictions.append({
                "jour": i,
                "date_predite": (dates[-1] + timedelta(days=i)).isoformat(),
                "alerte_predite": round(clamp(pred_alerte * ajust, 0.0, 10.0), 2),
                "energie_predite": round(clamp(pred_energie, 0.0, 100.0), 2),
                "risque_pic": self._risque_pic(pred_alerte, zone.volatilite),
                "confiance": round(self._confiance(len(alertes), zone.volatilite, i), 2)
            })

        return {
            "zone_id": zone.id, "sujet": zone.sujet, "horizon_effectif": self.horizon,
            "avertissement": "Prédiction à court terme uniquement (≤7 jours).",
            "tendance_actuelle": {"direction": "hausse" if coeff_alerte[0] > 0.05 else "baisse" if coeff_alerte[0] < -0.05 else "stable",
                                  "pente": float(coeff_alerte[0])},
            "predictions": predictions,
            "recommandations_anticipation": self._recommandations(predictions, zone)
        }

    def _ajustement_hebdo(self, jour_futur: int, dates: List[dt.datetime], valeurs: List[float]) -> float:
        if len(dates) < 14:
            return 1.0

        patterns = {i: [] for i in range(7)}
        for d, v in zip(dates, valeurs):
            patterns[d.weekday()].append(v)

        moyennes = {j: safe_mean(vs) for j, vs in patterns.items() if vs}
        if not moyennes:
            return 1.0

        moy_glob = safe_mean(list(moyennes.values()))
        if moy_glob == 0:
            return 1.0

        j_futur = (dates[-1].weekday() + jour_futur) % 7
        return clamp(moyennes.get(j_futur, moy_glob) / moy_glob, 0.7, 1.3)

    def _risque_pic(self, val: float, vol: float) -> str:
        if val >= 8 and vol > 0.3:
            return "très_élevé"
        if val >= 7 and vol > 0.2:
            return "élevé"
        if val >= 6:
            return "modéré"
        return "faible"

    def _confiance(self, n_points: int, vol: float, horizon: int) -> float:
        return clamp((min(1.0, n_points / 20.0)) * (1.0 - min(1.0, vol * 2.0)) * max(0.1, 1.0 - (horizon - 1) * 0.12), 0.05, 0.90)

    def _recommandations(self, predictions: List[Dict[str, Any]], zone: ZoneDeTension) -> List[str]:
        recs = []
        pics = [p for p in predictions if p.get("risque_pic") in ("élevé", "très_élevé")]
        if pics:
            recs.append(f"Préparer une réponse pour {len(pics)} pic(s) à haut risque dans les {self.horizon} jours")
        if predictions and predictions[-1]["alerte_predite"] > predictions[0]["alerte_predite"]:
            recs.append("Augmenter la fréquence de surveillance (passer à quotidienne)")
        if zone.resilience_narrative < 0.5:
            recs.append("Diversifier les sources de monitoring (faible résilience)")
        if zone.formes_opacite_detectees:
            ops = ", ".join(op.value for op in zone.formes_opacite_detectees[:3])
            recs.append(f"Préparer des clarifications pour : {ops}")
        return recs[:5]