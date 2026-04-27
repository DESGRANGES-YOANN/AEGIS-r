"""
AEGIS-Γ - Module AI-Generated Content Detector (Module 19)
"""

import re
from typing import Dict, Any

from aegis_gamma.core.models import FragmentNarratif
from aegis_gamma.core.utils import clamp


class DetecteurAIGenerated:
    """Détection de contenu généré par IA"""
    
    _PATTERNS_IA = [r"en tant qu'IA", r"je suis un modèle de langage", r"je n'ai pas de connaissances",
                    r"selon mes données d'entraînement", r"je ne peux pas générer"]
    
    def analyser(self, fragment: FragmentNarratif) -> Dict[str, Any]:
        """Détecte si le contenu est généré par IA"""
        texte = fragment.contenu.lower()
        score = 0.0
        for pattern in self._PATTERNS_IA:
            if re.search(pattern, texte):
                score += 0.3
        mots = texte.split()
        if len(mots) > 100:
            if len(set(mots)) / len(mots) < 0.3:
                score += 0.2
        score = clamp(score, 0.0, 1.0)
        return {"score_generation_ia": round(score, 3), "est_ia": score > 0.6, "confiance": round(0.5 + score * 0.3, 2),
                "recommandation": "Contenu suspect - vérifier l'authenticité" if score > 0.5 else "Contenu probablement authentique"}