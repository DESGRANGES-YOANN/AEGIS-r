"""
AEGIS-Γ - Module Harm & Impact Assessor (Module 21)
"""

from typing import Dict, Any

from aegis_gamma.core.enums import TypeOpacite, TypeTension
from aegis_gamma.core.models import ZoneDeTension


class HarmImpactAssessor:
    """Évaluation du dommage potentiel"""
    
    _POIDS = {"sante_publique": 0.35, "cohesion_sociale": 0.25, "confiance_institutionnelle": 0.20, "securite": 0.10, "economie": 0.10}
    
    def evaluer(self, zone: ZoneDeTension) -> Dict[str, Any]:
        """Évalue l'impact potentiel d'une zone"""
        scores = {}
        if any(m in zone.sujet.lower() for m in ["vaccin", "covid", "sante", "médicament"]):
            scores["sante_publique"] = min(1.0, zone.niveau_alerte / 8.0)
        if zone.repartition_tensions.get(TypeTension.SOCIALE, 0) > 0.6:
            scores["cohesion_sociale"] = zone.niveau_alerte / 10.0
        if TypeOpacite.ABSENCE_SOURCE in zone.formes_opacite_detectees:
            scores["confiance_institutionnelle"] = 0.7
        if zone.niveau_alerte > 7:
            scores["securite"] = zone.niveau_alerte / 10.0
        impact_total = sum(scores.get(d, 0) * self._POIDS.get(d, 0.1) for d in self._POIDS)
        niveau = "critique" if impact_total > 0.8 else "élevé" if impact_total > 0.6 else "modéré" if impact_total > 0.4 else "faible"
        return {"impact_par_domaine": scores, "impact_total": round(impact_total, 3), "niveau": niveau,
                "recommandation": f"Priorité {niveau} - intervention recommandée" if impact_total > 0.5 else "Surveillance normale"}