"""
AEGIS-Γ - Module Optimiseur auto-adaptatif
"""

from typing import Any, Dict, List, Optional

import numpy as np

from aegis_gamma.core.utils import LOGGER, now_iso, safe_mean, safe_std, clamp


class OptimiseurAutoAdaptatif:
    """Optimisation auto-adaptative des paramètres"""

    OBJECTIFS = {"detection_precoce": {"ponderation": {"precision": 0.3, "rappel": 0.7}},
                 "precision_maximale": {"ponderation": {"precision": 0.8, "rappel": 0.2}},
                 "couverture_maximale": {"ponderation": {"precision": 0.2, "rappel": 0.8}},
                 "equilibre": {"ponderation": {"precision": 0.5, "rappel": 0.5}}}

    PARAMS_DEF = {"seuil_alerte": {"min": 0.0, "max": 10.0, "type": "continu", "defaut": 5.0},
                  "seuil_coherence": {"min": 0.0, "max": 1.0, "type": "continu", "defaut": 0.6},
                  "seuil_charge": {"min": 0.0, "max": 10.0, "type": "continu", "defaut": 5.0},
                  "poids_divergence": {"min": 0.0, "max": 1.0, "type": "continu", "defaut": 0.7},
                  "poids_emotion": {"min": 0.0, "max": 1.0, "type": "continu", "defaut": 0.3},
                  "fenetre_temps_analyse": {"min": 1, "max": 30, "type": "discret", "defaut": 7},
                  "seuil_validation": {"min": 1, "max": 5, "type": "discret", "defaut": 3}}

    def __init__(self, objectif: str = "detection_precoce", seed: Optional[int] = None):
        self.objectif = objectif
        self.rng = np.random.default_rng(seed)
        self.historique = []
        self.cache_configs = {}
        self.max_historique = 500

    def definir_objectif(self, obj: str) -> bool:
        if obj in self.OBJECTIFS:
            self.objectif = obj
            return True
        return False

    def evaluer_performance(self, parametres: Dict[str, Any], resultats: Dict[str, Any]) -> Dict[str, Any]:
        metriques = self._extraire_metriques(resultats)
        score = self._score(metriques)
        entree = {"date": now_iso(), "parametres": parametres, "metriques": metriques,
                  "score_performance": score, "objectif": self.objectif}
        self.historique.append(entree)
        if len(self.historique) > self.max_historique:
            self.historique = self.historique[-self.max_historique:]
        return {"score": score, "metriques": metriques, "evaluation": self._eval_relative(score),
                "recommandations_ajustement": self._recommandations_ajust(metriques, score)}

    def _extraire_metriques(self, r: Dict[str, Any]) -> Dict[str, float]:
        precision = r.get("validation", {}).get("confiance_validation", 0.0) / 100.0
        rappel = min(1.0, len(r.get("zone_tension", {}).get("formes_opacite", [])) / 10.0)
        p_r = precision + rappel
        f1 = (2 * precision * rappel / p_r) if p_r > 0 else 0.0
        return {"precision": precision, "rappel": rappel, "f1_score": f1,
                "faux_positifs": max(0.0, 1.0 - (r.get("score_confiance", 0.0) / 10.0)),
                "faux_negatifs": max(0.0, (10.0 - r.get("zone_tension", {}).get("niveau_alerte", 0.0)) / 10.0),
                "temps_detection": 1.0 / (r.get("zone_tension", {}).get("niveau_alerte", 1.0) + 0.1)}

    def _score(self, m: Dict[str, float]) -> float:
        obj = self.objectif
        if obj == "detection_precoce":
            return float(clamp(m["rappel"] * 0.5 + m["temps_detection"] * 0.4 - m["faux_positifs"] * 0.1, 0, 1))
        if obj == "precision_maximale":
            return float(clamp(m["precision"] * 0.7 - m["faux_positifs"] * 0.3, 0, 1))
        if obj == "couverture_maximale":
            return float(clamp(m["rappel"] * 0.7 - m["faux_negatifs"] * 0.3, 0, 1))
        return float(clamp(m["f1_score"], 0, 1))

    def _eval_relative(self, score: float) -> Dict[str, Any]:
        if len(self.historique) < 5:
            return {"statut": "donnees_insuffisantes"}
        recents = [e["score_performance"] for e in self.historique[-10:]]
        moy = safe_mean(recents)
        if len(recents) >= 3:
            coeff = float(np.polyfit(np.arange(len(recents)), recents, 1)[0])
            tendance = "amélioration" if coeff > 0.01 else "dégradation" if coeff < -0.01 else "stable"
        else:
            tendance = "stable"
        position = ("excellente" if score >= max(recents) * 0.95 else "bonne" if score >= moy else "médiocre")
        return {"score_actuel": score, "moyenne_recente": moy, "position_relative": position,
                "tendance": tendance, "ecart_moyenne": score - moy}

    def _recommandations_ajust(self, m: Dict[str, float], score: float) -> List[str]:
        recs = []
        if m["precision"] < 0.6:
            recs += ["Augmenter les seuils de validation", "Renforcer les vérifications de cohérence"]
        if m["rappel"] < 0.5:
            recs += ["Baisser les seuils d'alerte", "Élargir la fenêtre d'analyse"]
        if m["faux_positifs"] > 0.4:
            recs.append("Augmenter le poids de la cohérence interne")
        return recs[:4]

    def optimiser_parametres(self, iterations: int = 20) -> Dict[str, Any]:
        if len(self.historique) < 10:
            return {"statut": "donnees_insuffisantes", "raison": f"{len(self.historique)} entrées (minimum 10)"}
        meilleurs = sorted(self.historique, key=lambda e: e.get("score_performance", 0), reverse=True)[:5]
        stats = self._analyser_params_optimaux(meilleurs)
        candidats = self._candidats(stats, iterations)
        meilleur = max(candidats, key=lambda c: c["score_estime"])
        cfg_id = f"CFG_{now_iso().replace(':', '-').replace('.', '-')}"
        self.cache_configs[cfg_id] = {"parametres": meilleur["params"], "score_estime": meilleur["score_estime"]}
        return {"statut": "optimisation_terminee", "config_id": cfg_id, "configuration_recommandee": meilleur["params"],
                "score_estime": meilleur["score_estime"], "nombre_configurations_testees": len(candidats),
                "recommandations_implementation": self._reco_impl(meilleur)}

    def _analyser_params_optimaux(self, configs: List[Dict]) -> Dict[str, Any]:
        agg = {}
        for c in configs:
            for k, v in c.get("parametres", {}).items():
                agg.setdefault(k, []).append(v)
        return {k: {"moyenne": safe_mean(vs), "std": safe_std(vs), "min": min(vs), "max": max(vs)} for k, vs in agg.items()}

    def _candidats(self, stats: Dict, iterations: int) -> List[Dict[str, Any]]:
        cands = []
        for _ in range(iterations):
            params = {}
            for pname, pdef in self.PARAMS_DEF.items():
                st = stats.get(pname, {"moyenne": pdef["defaut"], "std": 0.0, "min": pdef["min"], "max": pdef["max"]})
                if pdef["type"] == "continu":
                    v = float(clamp(self.rng.normal(st["moyenne"], max(st["std"] * 0.5, 0.01)), pdef["min"], pdef["max"]))
                else:
                    v = int(clamp(round(self.rng.normal(st["moyenne"], max(st["std"], 0.5))), pdef["min"], pdef["max"]))
                params[pname] = v
            sc = safe_mean([1.0 - abs(params[k] - stats[k]["moyenne"]) / max(stats[k]["max"] - stats[k]["min"], 1e-6)
                           for k in params if k in stats], 0.5)
            cands.append({"params": params, "score_estime": sc})
        return cands

    def _reco_impl(self, candidat: Dict) -> List[str]:
        recs = []
        for k, v in candidat["params"].items():
            defaut = self.PARAMS_DEF[k]["defaut"]
            rang = self.PARAMS_DEF[k]["max"] - self.PARAMS_DEF[k]["min"]
            if abs(v - defaut) > rang * 0.2:
                pct = ((v - defaut) / max(defaut, 1e-6)) * 100
                recs.append(f"Ajuster {k} : {defaut:.2f} → {v:.2f} ({pct:+.0f}%)")
        if not recs:
            recs.append("Configuration proche des valeurs par défaut")
        recs += [f"Objectif : {self.objectif}", "Surveiller les performances après implémentation"]
        return recs

    def rapport_optimisation(self) -> Dict[str, Any]:
        if not self.historique:
            return {"statut": "aucune_donnee"}
        scores = [e["score_performance"] for e in self.historique]
        coeff = float(np.polyfit(np.arange(len(scores)), scores, 1)[0]) if len(scores) >= 5 else 0.0
        tendance = "amélioration" if coeff > 0.001 else "dégradation" if coeff < -0.001 else "stable"
        return {"statistiques_globales": {"nombre_evaluations": len(scores), "score_moyen": safe_mean(scores),
                                          "score_max": max(scores), "score_min": min(scores), "tendance": tendance},
                "objectif_actuel": self.objectif, "configurations_cache": list(self.cache_configs.keys())[:5]}