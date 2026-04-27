"""
AEGIS-Γ - Module Analyseur de résilience (Gini corrigé)
"""

from collections import Counter
from typing import Any, Dict, List

import numpy as np

from aegis_gamma.core.enums import TypeSource
from aegis_gamma.core.models import FragmentNarratif, ZoneDeTension
from aegis_gamma.core.utils import safe_mean, safe_std, clamp


class AnalyseurResilience:
    """Analyse approfondie de la résilience narrative"""

    def analyser_resilience_profonde(self, zone: ZoneDeTension, fragments: List[FragmentNarratif]) -> Dict[str, Any]:
        if not fragments:
            return {"score_resilience": 0.5}

        # Indice de Gini corrigé pour la diversité des sources
        compteurs = Counter(f.type_source for f in fragments)
        total = len(fragments)
        props = np.array([c / total for c in compteurs.values()])

        if len(props) <= 1:
            gini = 0.0
            gini_norm = 0.0
        else:
            gini = 1.0 - np.sum(props ** 2)
            gini_norm = gini / (1.0 - 1.0 / len(props))

        # Stabilité émotionnelle
        stabilite = 1.0 - min(1.0, safe_std([f.charge_emotionnelle for f in fragments]) / 5.0)

        # Cohérence moyenne
        coherence = safe_mean([f.coherence_interne for f in fragments], 0.5)

        # Score composite
        score = (1.0 - gini_norm) * 0.3 + stabilite * 0.35 + coherence * 0.35

        categorie = ("très_élevée" if score >= 0.8 else "élevée" if score >= 0.6 else
                    "modérée" if score >= 0.4 else "faible" if score >= 0.2 else "très_faible")

        return {"score_resilience": round(float(score), 3), "categorie_resilience": categorie,
                "gini": round(float(gini_norm), 3), "stabilite_emotionnelle": round(stabilite, 3),
                "coherence_moyenne": round(coherence, 3), "recommandations": self._recommandations(score)}

    def _recommandations(self, score: float) -> List[str]:
        recs = []
        if score < 0.4:
            recs.append("Revue complète de la stratégie narrative nécessaire")
            recs.append("Étude approfondie des causes de faible résilience")
        elif score < 0.6:
            recs.append("Plan d'amélioration progressive de la résilience")
        else:
            recs.append("Maintenir et surveiller la résilience narrative")
        return recs