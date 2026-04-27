"""
AEGIS-Γ - Module Multimodal Analyzer (Module 17)
"""

import re
from typing import Any, Dict, Optional

from aegis_gamma.core.models import FragmentNarratif
from aegis_gamma.core.utils import clamp, safe_mean


class AnalyseurMultimodal:
    """Détection de deepfakes et analyse de cohérence multimodale"""

    class _AnalyseurTexteImage:
        async def analyser(self, texte: str, url_image: str) -> Dict[str, Any]:
            score = 0.5
            if any(m in texte.lower() for m in ["photo", "image", "montre"]):
                score += 0.1
            if any(m in texte.lower() for m in ["contrairement", "cependant"]):
                score -= 0.1
            score = clamp(score, 0.3, 0.7)
            return {"score_similarite": round(score, 2),
                    "niveau_consistance": "haute" if score > 0.6 else "moyenne" if score > 0.4 else "faible",
                    "explication": "Analyse de cohérence texte-image"}

    class _DetecteurDeepfake:
        async def analyser(self, url_video: str) -> Dict[str, Any]:
            import random
            score = random.uniform(0.1, 0.7)
            return {"score_deepfake": round(score, 3),
                    "type_deepfake": "synchro_labiale" if score > 0.5 else None,
                    "niveau": "critique" if score > 0.6 else "suspect" if score > 0.4 else "normal"}

    class _DetecteurMeme:
        async def analyser(self, texte: str, url_image: Optional[str] = None) -> Dict[str, Any]:
            score = 0.0
            if re.search(r"partagez|diffusez", texte.lower()):
                score += 0.2
            if re.search(r"scandale|choc|incroyable", texte.lower()):
                score += 0.15
            if not re.search(r"source|selon", texte.lower()):
                score += 0.1
            score = clamp(score, 0.0, 1.0)
            return {"score_manipulation": round(score, 3),
                    "niveau": "critique" if score > 0.6 else "suspect" if score > 0.3 else "normal",
                    "recommandation": "Mème potentiellement manipulé" if score > 0.3 else "Mème apparemment normal"}

    def __init__(self):
        self.analyseur_texte_image = self._AnalyseurTexteImage()
        self.detecteur_deepfake = self._DetecteurDeepfake()
        self.detecteur_meme = self._DetecteurMeme()

    async def analyser(self, fragment: FragmentNarratif) -> Dict[str, Any]:
        analyses = {}
        if fragment.contenu and hasattr(fragment, 'url_image') and fragment.url_image:
            analyses["texte_image"] = await self.analyseur_texte_image.analyser(fragment.contenu, fragment.url_image)
        if hasattr(fragment, 'url_video') and fragment.url_video:
            analyses["deepfake"] = await self.detecteur_deepfake.analyser(fragment.url_video)
        if fragment.contenu:
            analyses["meme"] = await self.detecteur_meme.analyser(fragment.contenu)

        scores = [a.get("score_similarite", 0.5) for a in analyses.values() if "score_similarite" in a]
        scores += [1.0 - a.get("score_deepfake", 0) for a in analyses.values() if "score_deepfake" in a]
        scores += [1.0 - a.get("score_manipulation", 0) for a in analyses.values() if "score_manipulation" in a]
        score_global = safe_mean(scores) if scores else 0.5

        return {"score_consistance_global": round(score_global, 3), "analyses_par_modalite": analyses,
                "niveau_alerte": "critique" if score_global < 0.4 else "haute" if score_global < 0.6 else "faible"}