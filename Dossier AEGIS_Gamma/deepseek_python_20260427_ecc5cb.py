"""
AEGIS-Γ - Module Argumentation Miner (Module 18)
"""

import re
from typing import Dict, List, Any


class ArgumentationMiner:
    """Extraction de structure argumentative et détection de fallacies"""
    
    _FALLACIES = {
        "ad_hominem": r"(tu es|vous êtes)\s+(ignorant|corrompu|naïf|stupide)",
        "appel_emotion": r"(pensez aux|imaginez|les pauvres)\s+(enfants|victimes|souffrance)",
        "pente_glissante": r"(si on accepte|bientôt|prochaine étape)",
        "homme_de_paille": r"(vous voulez dire que|donc selon vous)"
    }
    
    def analyser(self, texte: str) -> Dict[str, Any]:
        """Analyse argumentative d'un texte"""
        phrases = [p.strip() for p in re.split(r'[.!?]+', texte) if len(p.strip()) > 20 and '?' not in p]
        fallacies = []
        for nom, pattern in self._FALLACIES.items():
            if re.search(pattern, texte, re.I):
                fallacies.append(nom)
        return {"nb_claims": len(phrases), "claims": phrases[:3], "fallacies_detectees": fallacies,
                "niveau_manipulation": "élevé" if len(fallacies) >= 2 else "modéré" if fallacies else "faible",
                "recommandations": self._recommandations(fallacies)}
    
    def _recommandations(self, fallacies: List[str]) -> List[str]:
        recs = []
        if "ad_hominem" in fallacies:
            recs.append("Éviter les attaques personnelles - répondre sur le fond")
        if "appel_emotion" in fallacies:
            recs.append("Vérifier les faits objectifs plutôt que de se fier à l'émotion")
        if "pente_glissante" in fallacies:
            recs.append("Demander des preuves du lien de causalité")
        return recs