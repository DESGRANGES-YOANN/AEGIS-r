"""
AEGIS-Γ - Système de contrôle narratif
Version: 4.0.0
"""

from aegis_gamma.core.enums import TypeOpacite, TypeSource, TypeTension, ProfilEthique, TypeSourceCredibilite
from aegis_gamma.core.models import FragmentNarratif, ZoneDeTension, PointTension, DecisionTraced
from aegis_gamma.orchestrator.systeme import SystemeControleNarratifV4

__version__ = "4.0.0"
__all__ = [
    "TypeOpacite",
    "TypeSource",
    "TypeTension",
    "ProfilEthique",
    "TypeSourceCredibilite",
    "FragmentNarratif",
    "ZoneDeTension",
    "PointTension",
    "DecisionTraced",
    "SystemeControleNarratifV4",
]