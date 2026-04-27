"""
AEGIS-Γ - Module Visualiseur cartographie
"""

from typing import List, Optional
import matplotlib.pyplot as plt

from aegis_gamma.core.models import ZoneDeTension


class VisualiseurCartographie:
    """Visualisation de la cartographie"""

    @staticmethod
    def generer_carte_thermique(zones: List[ZoneDeTension], titre: str = "Carte thermique"):
        if not zones:
            return None

        alertes = [z.niveau_alerte for z in zones]
        energies = [z.energie_estimee for z in zones]
        sujets = [z.sujet for z in zones]

        couleurs = ["red" if a >= 8 else "orange" if a >= 6 else "yellow" if a >= 4 else "green" for a in alertes]
        tailles = [max(50, e * 5.0) for e in energies]

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.scatter(alertes, energies, s=tailles, c=couleurs, alpha=0.6, edgecolors="black")

        for i, sujet in enumerate(sujets):
            ax.annotate(sujet[:20], (alertes[i], energies[i]), fontsize=9, ha="center", va="bottom")

        ax.set_xlabel("Niveau d'alerte (0-10)")
        ax.set_ylabel("Énergie estimée")
        ax.set_title(titre, fontweight="bold")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig