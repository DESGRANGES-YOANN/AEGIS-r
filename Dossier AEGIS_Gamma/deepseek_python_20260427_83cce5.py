"""
AEGIS-Γ - Module Prebunking & Inoculation Engine (Module 22)
"""

from typing import Dict, Any, List, Optional

from aegis_gamma.core.models import ZoneDeTension


class PrebunkingEngine:
    """Génération automatique de pré-bunking"""
    
    def generer(self, zone: ZoneDeTension, techniques: Optional[List[str]] = None) -> Dict[str, Any]:
        """Génère un pré-bunking adapté"""
        if techniques is None:
            techniques = ["manipulation narrative"]
        technique = techniques[0] if techniques else "manipulation narrative"
        avertissement = f"⚠️ Attention : Ce récit utilise la technique de {technique}"
        formats = {
            "short": avertissement,
            "medium": f"{avertissement}\n\nCette technique consiste à influencer votre perception. Vérifiez toujours les sources.",
            "long": f"{avertissement}\n\nLa technique de {technique} est couramment utilisée pour manipuler l'opinion.\n\n"
                    f"Comment s'en protéger ?\n"
                    f"1. Vérifier les sources originales\n"
                    f"2. Chercher des avis contradictoires\n"
                    f"3. Rester critique face aux arguments émotionnels",
            "video_script": f"[TEXTE À L'ÉCRAN] ATTENTION - Technique de {technique.upper()}\n"
                            f"[VOIX OFF] Vous êtes peut-être en train de lire une manipulation narrative.\n"
                            f"[TEXTE À L'ÉCRAN] {technique} = tentative d'influence\n"
                            f"[VOIX OFF] Prenez du recul et vérifiez les faits."}
        return {"technique": technique, "niveau_alerte": zone.niveau_alerte,
                "formats": formats, "recommandation": formats["short"]}