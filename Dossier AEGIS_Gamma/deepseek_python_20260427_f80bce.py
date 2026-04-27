"""
AEGIS-Γ - Module Apprentissage des patterns de brouillage
"""

from typing import Dict, List, Tuple

from aegis_gamma.core.enums import TypeSource
from aegis_gamma.core.utils import safe_mean, now_iso
from aegis_gamma.modules.cartographe import CartographeBrouillage


class ApprentissageBrouillage:
    """Apprentissage des patterns de brouillage"""

    def __init__(self):
        self.patterns_appris: List[Dict] = []
        self.efficacite_patterns: Dict[str, float] = {}
        self._patterns_communs = {
            "long_terme": "Brouillage persistant",
            "multi_canal": "Utilisation multi-canal",
            "emotion_forte": "Émotion forte",
            "complexite": "Surcomplexification technique",
            "memetisation": "Mémétisation / viralité",
        }

    def analyser_brouillage_reussi(self, sujet: str, cartographe: CartographeBrouillage,
                                   duree_jours: int = 365) -> List[str]:
        fragments = [f for f in cartographe.fragments.values() if f.sujet == sujet]
        if not fragments:
            return ["Données insuffisantes"]

        insights = []
        if duree_jours >= 180:
            insights.append(self._patterns_communs["long_terme"])
        if len(set(f.type_source for f in fragments)) >= 4:
            insights.append(f"{self._patterns_communs['multi_canal']} ({len(set(f.type_source for f in fragments))} canaux)")
        charge_moy = safe_mean([f.charge_emotionnelle for f in fragments])
        if charge_moy >= 6:
            insights.append(f"{self._patterns_communs['emotion_forte']} ({charge_moy:.1f}/10)")
        mots_tech = sum(1 for f in fragments for mot in ("quantique", "algorithme", "cryptographique", "turing", "blockchain")
                        if mot in f.contenu.lower())
        if mots_tech >= 5:
            insights.append(self._patterns_communs["complexite"])
        if any(f.type_source == TypeSource.MEME for f in fragments):
            insights.append(self._patterns_communs["memetisation"])

        if insights:
            self.patterns_appris.append({"sujet": sujet, "date_analyse": now_iso(),
                "duree_jours": duree_jours, "patterns_detectes": insights, "fragments_analyses": len(fragments)})
            for k, desc in self._patterns_communs.items():
                if any(desc in s for s in insights):
                    self.efficacite_patterns[k] = self.efficacite_patterns.get(k, 0.5) + 0.1

        return insights if insights else ["Aucun pattern fort détecté"]

    def get_patterns_efficaces(self, top_n: int = 3) -> List[Tuple[str, float]]:
        return sorted(self.efficacite_patterns.items(), key=lambda x: x[1], reverse=True)[:top_n]