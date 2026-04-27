"""
AEGIS-Γ - Modèles de données centraux
"""

from __future__ import annotations

import datetime as dt
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from aegis_gamma.core.enums import TypeOpacite, TypeSource, TypeTension
from aegis_gamma.core.utils import CONFIG, now, clamp


@dataclass
class FragmentNarratif:
    """Fragment narratif individuel - optimisé mémoire"""
    __slots__ = ('id', 'sujet', 'type_source', 'contenu', 'charge_emotionnelle',
                 'date_collecte', 'coherence_interne', 'divergence_externe',
                 'auteur', 'url_source', 'langue', 'pays', 'image_hash')
    
    id: str
    sujet: str
    type_source: TypeSource
    contenu: str
    charge_emotionnelle: float
    date_collecte: dt.datetime
    coherence_interne: float = 0.5
    divergence_externe: float = 0.5
    auteur: Optional[str] = None
    url_source: Optional[str] = None
    langue: str = "fr"
    pays: str = "France"
    image_hash: Optional[str] = None
    
    def to_dict(self, truncate: int = 500) -> Dict[str, Any]:
        c = self.contenu[:truncate] + "..." if len(self.contenu) > truncate else self.contenu
        from aegis_gamma.core.enums import _TYPE_SOURCE_LOOKUP
        return {
            "id": self.id, "sujet": self.sujet, "type_source": self.type_source.value,
            "contenu": c, "charge_emotionnelle": self.charge_emotionnelle,
            "date_collecte": self.date_collecte.isoformat(),
            "coherence_interne": self.coherence_interne,
            "divergence_externe": self.divergence_externe,
            "auteur": self.auteur, "url_source": self.url_source,
            "langue": self.langue, "pays": self.pays
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FragmentNarratif":
        from aegis_gamma.core.enums import _TYPE_SOURCE_LOOKUP
        return cls(
            id=data["id"], sujet=data["sujet"],
            type_source=_TYPE_SOURCE_LOOKUP.get(data["type_source"], TypeSource.ARTICLE_PRESSE),
            contenu=data["contenu"], charge_emotionnelle=float(data["charge_emotionnelle"]),
            date_collecte=dt.datetime.fromisoformat(data["date_collecte"]),
            coherence_interne=float(data.get("coherence_interne", 0.5)),
            divergence_externe=float(data.get("divergence_externe", 0.5)),
            auteur=data.get("auteur"), url_source=data.get("url_source"),
            langue=data.get("langue", "fr"), pays=data.get("pays", "France")
        )


@dataclass
class PointTension:
    """Point d'historique d'une zone de tension"""
    __slots__ = ('date', 'niveau_alerte', 'energie_estimee', 'fragments_count', 'formes_opacite', 'resilience_narrative')
    
    date: dt.datetime
    niveau_alerte: float
    energie_estimee: float
    fragments_count: int
    formes_opacite: List[str]
    resilience_narrative: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {"date": self.date.isoformat(), "niveau_alerte": self.niveau_alerte,
                "energie_estimee": self.energie_estimee, "fragments_count": self.fragments_count,
                "formes_opacite": self.formes_opacite, "resilience_narrative": self.resilience_narrative}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PointTension":
        return cls(date=dt.datetime.fromisoformat(data["date"]), niveau_alerte=float(data["niveau_alerte"]),
                   energie_estimee=float(data["energie_estimee"]), fragments_count=int(data["fragments_count"]),
                   formes_opacite=data["formes_opacite"], resilience_narrative=float(data.get("resilience_narrative", 1.0)))


@dataclass
class ZoneDeTension:
    """Zone de tension narrative avec historique"""
    __slots__ = ('id', 'sujet', 'fragments_ids', 'niveau_alerte', 'energie_estimee',
                 'formes_opacite_detectees', 'ratio_divergences_par_fragment',
                 'date_creation', 'date_derniere_maj', 'historique_tension',
                 'repartition_tensions', 'resilience_narrative', 'tendance_alerte', 'volatilite')
    
    id: str
    sujet: str
    fragments_ids: List[str]
    niveau_alerte: float
    energie_estimee: float
    formes_opacite_detectees: List[TypeOpacite]
    ratio_divergences_par_fragment: float
    date_creation: dt.datetime
    date_derniere_maj: Optional[dt.datetime] = None
    historique_tension: Deque[PointTension] = field(default_factory=lambda: deque(maxlen=CONFIG.max_historique_points))
    repartition_tensions: Dict[TypeTension, float] = field(default_factory=dict)
    resilience_narrative: float = 1.0
    tendance_alerte: float = 0.0
    volatilite: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "sujet": self.sujet, "n_fragments": len(self.fragments_ids),
            "niveau_alerte": self.niveau_alerte, "energie_estimee": self.energie_estimee,
            "formes_opacite": [op.value for op in self.formes_opacite_detectees],
            "ratio_divergence": self.ratio_divergences_par_fragment,
            "date_creation": self.date_creation.isoformat(),
            "date_derniere_maj": self.date_derniere_maj.isoformat() if self.date_derniere_maj else None,
            "historique_points": len(self.historique_tension),
            "repartition_tensions": {k.value: v for k, v in self.repartition_tensions.items()},
            "resilience_narrative": self.resilience_narrative,
            "tendance_alerte": self.tendance_alerte, "volatilite": self.volatilite
        }
    
    def ajouter_point_historique(self, fragments_count: int, resilience: Optional[float] = None) -> None:
        point = PointTension(date=now(), niveau_alerte=self.niveau_alerte, energie_estimee=self.energie_estimee,
                             fragments_count=fragments_count, formes_opacite=[op.value for op in self.formes_opacite_detectees],
                             resilience_narrative=resilience if resilience is not None else self.resilience_narrative)
        self.historique_tension.append(point)
        if len(self.historique_tension) >= 2:
            self._calculer_dynamique()
    
    def _calculer_dynamique(self) -> None:
        alertes = [p.niveau_alerte for p in list(self.historique_tension)[-10:]]
        if len(alertes) >= 2:
            import numpy as np
            x = np.arange(len(alertes))
            self.tendance_alerte = clamp(float(np.polyfit(x, alertes, 1)[0]) / 2.0, -1.0, 1.0)
        if len(alertes) >= 3:
            import numpy as np
            self.volatilite = float(np.std(alertes)) / 5.0


@dataclass
class DecisionTraced:
    """Décision tracée pour audit"""
    __slots__ = ('id', 'date', 'sujet', 'zone_id', 'niveau_alerte', 'score_confiance',
                 'version_regles', 'parametres_decision', 'alternatives', 'validation_humaine', 'commentaires')
    
    id: str
    date: dt.datetime
    sujet: str
    zone_id: str
    niveau_alerte: float
    score_confiance: float
    version_regles: str = "4.0.0"
    parametres_decision: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    validation_humaine: Optional[Dict[str, Any]] = None
    commentaires: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "date": self.date.isoformat(), "sujet": self.sujet,
                "zone_id": self.zone_id, "niveau_alerte": self.niveau_alerte,
                "score_confiance": self.score_confiance, "version_regles": self.version_regles,
                "parametres_decision": self.parametres_decision, "alternatives_count": len(self.alternatives),
                "validation_humaine": self.validation_humaine, "commentaires": self.commentaires}