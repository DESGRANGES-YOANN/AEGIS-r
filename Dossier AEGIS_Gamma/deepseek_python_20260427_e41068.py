"""
AEGIS-Γ - Module Narrative Framing Analyzer (Module 20)
"""

import re
from typing import Dict, List, Any

from aegis_gamma.core.models import ZoneDeTension, FragmentNarratif


class NarrativeFramingAnalyzer:
    """Analyse des cadres narratifs (théorie du cadrage)"""
    
    _FRAMES = {
        "problem_definition": r"(menace|crise|danger|urgence|alerte)",
        "causal_interpretation": r"(responsable|cause|origine|à cause de)",
        "moral_evaluation": r"(bien|mal|juste|injuste|devoir)",
        "treatment_recommendation": r"(solution|il faut|nous devons|action)"
    }
    
    def analyser(self, zone: ZoneDeTension, fragments: List[FragmentNarratif]) -> Dict[str, Any]:
        """Analyse le cadrage narratif d'une zone"""
        if not fragments:
            return {"cadres_detectes": {k: 0 for k in self._FRAMES}, "alerte_cadrage": "normal"}
        texte = " ".join(f.contenu.lower() for f in fragments[:10])
        cadres = {k: 0.5 for k in self._FRAMES}
        for cadre, pattern in self._FRAMES.items():
            matches = len(re.findall(pattern, texte))
            cadres[cadre] = min(1.0, matches / 5)
        alerte = "normal"
        if cadres.get("moral_evaluation", 0) > 0.7 and cadres.get("causal_interpretation", 0) < 0.3:
            alerte = "Jugement moral sans cause identifiée - manipulation potentielle"
        return {"cadres_detectes": cadres, "alerte_cadrage": alerte, "cadre_dominant": max(cadres, key=cadres.get)}