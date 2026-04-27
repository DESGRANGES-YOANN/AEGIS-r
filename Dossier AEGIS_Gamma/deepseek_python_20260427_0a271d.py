"""
AEGIS-Γ - Module Priorisation stratégique
"""

from typing import Any, Dict, List

from aegis_gamma.core.models import ZoneDeTension
from aegis_gamma.core.utils import now


class PriorisationStrategique:
    """Priorisation des investigations"""

    def __init__(self):
        self.criteres = {"urgence": 0.30, "impact_social": 0.25, "ressources_requises": 0.20,
                         "potentiel_revelation": 0.15, "fenetre_temps": 0.10}

    def generer_ordre_investigation(self, zones: List[ZoneDeTension]) -> List[Dict[str, Any]]:
        if not zones:
            return []
        resultats = []
        for z in zones:
            scores = {
                "urgence": min(1.0, z.niveau_alerte / 10.0),
                "impact_social": min(1.0, z.energie_estimee / 100.0),
                "ressources_requises": max(0.2, 1.0 - min(1.0, len(z.formes_opacite_detectees) / 5.0)),
                "potentiel_revelation": min(1.0, z.ratio_divergences_par_fragment),
                "fenetre_temps": self._score_fenetre(z)
            }
            score_total = sum(scores[k] * self.criteres[k] for k in self.criteres)
            resultats.append({"zone": z, "score_total": round(float(score_total), 3),
                              "scores_detail": {k: round(float(v), 3) for k, v in scores.items()},
                              "raison_priorite": self._raison(scores)})
        return sorted(resultats, key=lambda x: x["score_total"], reverse=True)

    def _score_fenetre(self, zone: ZoneDeTension) -> float:
        jours = (now() - zone.date_creation).days
        return 1.0 if jours < 7 else 0.7 if jours < 30 else 0.4 if jours < 90 else 0.2

    def _raison(self, scores: Dict[str, float]) -> str:
        crit = max(scores.items(), key=lambda x: x[1])[0]
        return {"urgence": "Niveau d'alerte nécessitant action rapide", "impact_social": "Impact sociétal potentiel élevé",
                "ressources_requises": "Investigation relativement accessible",
                "potentiel_revelation": "Bon potentiel de clarification",
                "fenetre_temps": "Fenêtre temporelle favorable"}.get(crit, "Priorité multi-critères")