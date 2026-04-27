"""
AEGIS-Γ - Module Gestionnaire de persistance
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from aegis_gamma.core.models import DecisionTraced, FragmentNarratif, ZoneDeTension
from aegis_gamma.core.utils import LOGGER, now_iso


class GestionnairePersistance:
    """Gestion de la persistance des données"""

    def __init__(self, dossier: str = "sauvegardes"):
        self.dossier = Path(dossier)
        self.dossier.mkdir(parents=True, exist_ok=True)

    def sauvegarder_etat(self, systeme, nom_fichier: Optional[str] = None) -> Path:
        from aegis_gamma.orchestrator.systeme import SystemeControleNarratifV4
        nom_fichier = nom_fichier or f"systeme_{now_iso().replace(':', '-')}.json"
        chemin = self.dossier / nom_fichier

        etat = {"version": "4.0.0", "date": now_iso(),
                "fragments": [f.to_dict() for f in systeme.cartographe.fragments.values()],
                "zones": [z.to_dict() for z in systeme.cartographe.zones_tension.values()],
                "decisions": [d.to_dict() for d in systeme.journal_decisions]}

        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(etat, f, ensure_ascii=False, indent=2)
        LOGGER.info("État sauvegardé : %s", chemin)
        return chemin

    def charger_etat(self, systeme, nom_fichier: str) -> bool:
        chemin = self.dossier / nom_fichier
        if not chemin.exists():
            LOGGER.error("Fichier non trouvé : %s", chemin)
            return False

        with open(chemin, "r", encoding="utf-8") as f:
            etat = json.load(f)

        systeme.cartographe.fragments.clear()
        systeme.cartographe.zones_tension.clear()
        systeme.journal_decisions.clear()

        for fd in etat.get("fragments", []):
            frag = FragmentNarratif.from_dict(fd)
            systeme.cartographe.fragments[frag.id] = frag
            systeme.cartographe.sujets_suivis.add(frag.sujet)

        for zd in etat.get("zones", []):
            zone = ZoneDeTension.from_dict(zd)
            systeme.cartographe.zones_tension[zone.id] = zone

        for dd in etat.get("decisions", []):
            from datetime import datetime
            systeme.journal_decisions.append(DecisionTraced(
                id=dd["id"], date=datetime.fromisoformat(dd["date"]), sujet=dd["sujet"],
                zone_id=dd["zone_id"], niveau_alerte=float(dd["niveau_alerte"]),
                score_confiance=float(dd["score_confiance"]), version_regles=dd.get("version_regles", "4.0.0"),
                parametres_decision=dd.get("parametres_decision", {}), commentaires=dd.get("commentaires", [])))

        LOGGER.info("État chargé depuis %s", chemin)
        return True