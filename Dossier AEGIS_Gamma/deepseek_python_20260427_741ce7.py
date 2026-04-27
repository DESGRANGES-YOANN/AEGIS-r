"""
AEGIS-Γ - Module Analyseur multilingue
"""

from typing import Any, Dict, List, Optional

from aegis_gamma.core.utils import safe_mean


class AnalyseurMultilingue:
    """Analyse des variations linguistiques et culturelles"""

    def __init__(self, langues_supportees: Optional[List[str]] = None):
        self.langues_supportees = langues_supportees or ["fr", "en", "es", "de", "ar", "zh"]
        self.dicos = {
            "fr": {"mots_sensibles": ["laïcité", "république", "égalité", "liberté"],
                   "concepts_cles": ["état-nation", "service public", "méritocratie"]},
            "en": {"mots_sensibles": ["freedom", "democracy", "constitution", "rights"],
                   "concepts_cles": ["free speech", "rule of law", "checks and balances"]},
            "es": {"mots_sensibles": ["dignidad", "justicia", "soberanía", "pueblo"],
                   "concepts_cles": ["estado de derecho", "bien común", "solidaridad"]},
        }

    def analyser_variations_linguistiques(self, sujet: str, fragments_multilingues: List[Dict[str, Any]]) -> Dict[str, Any]:
        par_langue = {}
        for frag in fragments_multilingues:
            lang = frag.get("langue", "inconnue")
            par_langue.setdefault(lang, []).append(frag)

        analyses = {lang: self._analyser_langue(lang, frags) for lang, frags in par_langue.items()}
        comparaison = self._comparer(analyses)
        manipulations = self._detecter_manipulations(fragments_multilingues)

        return {"sujet": sujet, "langues_analysees": list(analyses.keys()), "analyses_par_langue": analyses,
                "comparaison_interlangue": comparaison, "manipulations_traduction": manipulations,
                "recommandations": self._recommandations(comparaison, manipulations)}

    def _analyser_langue(self, langue: str, fragments: List[Dict[str, Any]]) -> Dict[str, Any]:
        texte = " ".join(f.get("contenu", "") for f in fragments).lower()
        dico = self.dicos.get(langue, {})
        detect = {"mots_sensibles": {m: texte.count(m.lower()) for m in dico.get("mots_sensibles", [])},
                  "concepts_cles": {c: texte.count(c.lower()) for c in dico.get("concepts_cles", [])}}
        total_mots = max(len(texte.split()), 1)
        specificite = sum(sum(detect[k].values()) for k in detect) / total_mots
        return {"nombre_fragments": len(fragments),
                "longueur_moyenne": sum(len(f.get("contenu", "")) for f in fragments) / max(len(fragments), 1),
                "detection_culturelle": detect, "specificite_culturelle": specificite,
                "niveau_localisation": "fort" if specificite > 0.05 else "modéré" if specificite > 0.02 else "faible"}

    def _comparer(self, analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        langues = list(analyses.keys())
        if len(langues) < 2:
            return {"statut": "comparaison_impossible"}

        comps = []
        for i in range(len(langues)):
            for j in range(i + 1, len(langues)):
                l1, l2 = langues[i], langues[j]
                a1, a2 = analyses[l1], analyses[l2]
                diff_spec = abs(a1["specificite_culturelle"] - a2["specificite_culturelle"])
                div = min(1.0, diff_spec * 10)
                comps.append({"langues": f"{l1}-{l2}", "divergence": div,
                              "niveau_divergence": "forte" if div > 0.7 else "modérée" if div > 0.4 else "faible"})

        plus_div = max(comps, key=lambda c: c["divergence"]) if comps else None
        moy_div = safe_mean([c["divergence"] for c in comps])

        return {"nombre_comparaisons": len(comps), "comparaisons_detaillees": comps, "paire_plus_divergente": plus_div,
                "conclusion": ("Narratives fortement différenciées" if moy_div > 0.6 else
                              "Variations culturelles modérées" if moy_div > 0.3 else "Narratives cohérentes entre langues")}

    def _detecter_manipulations(self, fragments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        manips = []
        groupes = {}
        for frag in fragments:
            sid = frag.get("source_originale_id") or frag.get("titre", "")[:50]
            groupes.setdefault(sid, []).append(frag)

        for sid, groupe in groupes.items():
            if len(groupe) < 2:
                continue
            langues = [f.get("langue") for f in groupe]
            contenus = [f.get("contenu", "") for f in groupe]
            if len(set(langues)) < 2:
                continue
            lons = [len(c) for c in contenus]
            if max(lons) > min(lons) * 2.0:
                manips.append({"source_id": sid, "type": "troncature_importante", "langues": langues,
                               "severite": "moyenne", "detail": f"Longueurs : {max(lons)} vs {min(lons)} chars"})
            for mot in ("non", "pas", "ne", "sans", "aucun"):
                presences = [mot in c.lower() for c in contenus]
                if any(presences) and not all(presences):
                    manips.append({"source_id": sid, "type": "omission_negation", "mot": mot,
                                   "langues_present": [l for l, p in zip(langues, presences) if p],
                                   "langues_absente": [l for l, p in zip(langues, presences) if not p],
                                   "severite": "haute"})
        return manips

    def _recommandations(self, comparaison: Dict, manipulations: List) -> List[str]:
        recs = []
        if "fortement différenciées" in comparaison.get("conclusion", ""):
            recs += ["Étudier les causes des différences culturelles importantes",
                     "Adapter la stratégie de communication par marché linguistique"]
        if manipulations:
            recs.append("Mettre en place un contrôle qualité des traductions")
            hautes = [m for m in manipulations if m.get("severite") == "haute"]
            if hautes:
                recs.append(f"Revérifier {len(hautes)} traduction(s) à haute sévérité")
        if not recs:
            recs += ["Maintenir la cohérence actuelle", "Surveiller régulièrement les variations"]
        return recs