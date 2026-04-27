"""
AEGIS-Γ - Module Analyseur de réseaux
"""

import re
from typing import Any, Dict, List
from urllib.parse import urlparse

from aegis_gamma.core.models import FragmentNarratif
from aegis_gamma.core.utils import LOGGER, now, safe_mean


class AnalyseurReseaux:
    """Analyse des réseaux de propagation"""

    def __init__(self):
        self.graphes: Dict[str, Dict[str, Any]] = {}

    def construire_graphe_propagation(self, fragments: List[FragmentNarratif]) -> Dict[str, Any]:
        graphe = {"noeuds": {}, "aretes": [], "metriques": {}, "influenceurs": []}

        def add(nid: str, ntype: str):
            graphe["noeuds"].setdefault(nid, {"type": ntype, "degree": 0})

        for frag in fragments:
            auteur = frag.auteur or "anonyme"
            add(auteur, "auteur")

            if frag.url_source:
                dom = urlparse(frag.url_source).netloc.replace("www.", "") or "domaine_inconnu"
                add(dom, "source")
                graphe["aretes"].append({"source": auteur, "cible": dom, "type": "publie_sur", "poids": frag.charge_emotionnelle})

            for ht in re.findall(r"#(\w+)", frag.contenu):
                add(ht, "hashtag")
                graphe["aretes"].append({"source": auteur, "cible": ht, "type": "utilise", "poids": 1.0})

        for e in graphe["aretes"]:
            for cle in ("source", "cible"):
                if e[cle] in graphe["noeuds"]:
                    graphe["noeuds"][e[cle]]["degree"] += 1

        graphe["metriques"] = self._metriques(graphe)
        graphe["influenceurs"] = self._influenceurs(graphe)

        gid = f"GRAPHE_{now().strftime('%Y%m%d_%H%M%S%f')}"
        self.graphes[gid] = graphe

        return {"id": gid, "resume": {"noeuds_total": len(graphe["noeuds"]), "aretes_total": len(graphe["aretes"]),
                                      "influenceurs": len(graphe["influenceurs"])}, "graphe": graphe}

    def analyser_patterns_coordination(self, graphe_id: str) -> Dict[str, Any]:
        if graphe_id not in self.graphes:
            return {"erreur": "Graphe non trouvé"}

        densite = self.graphes[graphe_id].get("metriques", {}).get("densite", 0.0)
        detecte = densite > 0.2
        from aegis_gamma.core.utils import clamp
        confiance = clamp(densite * 3.0, 0.0, 1.0)
        niveau = "forte" if confiance > 0.7 else "moderee" if confiance > 0.4 else "faible" if detecte else "aucun"

        return {"evaluation_coordination": {"niveau": niveau, "confiance": confiance, "densite_reseau": densite,
                "recommandation": "Surveillance accrue" if detecte else "Pas de signal de coordination structurelle"}}

    def _metriques(self, g: Dict[str, Any]) -> Dict[str, Any]:
        n = len(g["noeuds"])
        m = len(g["aretes"])
        densite = (2.0 * m) / (n * (n - 1)) if n > 1 else 0.0
        degres = [d["degree"] for d in g["noeuds"].values()]
        return {"noeuds": n, "aretes": m, "densite": densite, "degre_moyen": safe_mean(degres)}

    def _influenceurs(self, g: Dict[str, Any]) -> List[Dict[str, Any]]:
        auteurs = [(nid, d["degree"]) for nid, d in g["noeuds"].items() if d["type"] == "auteur"]
        auteurs.sort(key=lambda x: x[1], reverse=True)
        return [{"auteur": a, "degre": d} for a, d in auteurs[:10]}