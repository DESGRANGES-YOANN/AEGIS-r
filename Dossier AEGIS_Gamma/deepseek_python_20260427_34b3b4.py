"""
AEGIS-Γ - Utilitaires centraux
"""

import datetime as dt
import hashlib
import logging
import re
from dataclasses import dataclass
from functools import wraps
from typing import List, Optional

import numpy as np


@dataclass
class AegisConfig:
    """Configuration centralisée du système"""
    max_total_fragments: int = 10000
    max_fragments_par_sujet: int = 1000
    max_len_contenu: int = 10000
    max_historique_points: int = 200
    seuil_alerte_critique: float = 8.0
    seuil_alerte_haute: float = 6.0
    seuil_alerte_moyenne: float = 4.0
    horizon_prediction_max: int = 7
    horizon_simulation_max: int = 30
    cache_size_embeddings: int = 1000
    cache_size_lru: int = 256
    http_timeout: int = 10
    http_pool_size: int = 10
    use_gpu: bool = False
    model_embeddings: str = "camembert-base"
    quantize_mlp: bool = True
    verbose: bool = False
    seed: Optional[int] = 42


CONFIG = AegisConfig()

# Précompilation regex
_RE_URL = re.compile(r'https?://[^\s]+')
_RE_CHIFFRES = re.compile(r'\d+(?:[.,]\d+)?\s?(?:%|€|\$|millions?|milliards?)')
_RE_CITATIONS = re.compile(r'"[^"]{10,}"')
_RE_REFERENCES = re.compile(r'\[\d+\]|\([A-Z][a-z]+,?\s+\d{4}\)')
_RE_HASHTAG = re.compile(r'#(\w+)')
_RE_EMAIL = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
_RE_DATE = re.compile(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b')


def setup_logging(verbose: bool = False) -> None:
    """Configure le système de logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    if verbose:
        logging.getLogger("aegis").debug("Mode verbose activé")


LOGGER = logging.getLogger("aegis")


def now() -> dt.datetime:
    """Retourne la date/heure courante"""
    return dt.datetime.now()


def now_iso() -> str:
    """Retourne la date/heure au format ISO"""
    return dt.datetime.now().isoformat()


def timedelta(**kwargs) -> dt.timedelta:
    """Factory pour timedelta"""
    return dt.timedelta(**kwargs)


def clamp(x: float, lo: float, hi: float) -> float:
    """Limite une valeur entre lo et hi"""
    return lo if x < lo else hi if x > hi else x


def safe_mean(values: List[float], default: float = 0.0) -> float:
    """Moyenne sécurisée"""
    return float(np.mean(values)) if values else default


def safe_std(values: List[float], default: float = 0.0) -> float:
    """Écart-type sécurisé"""
    return float(np.std(values)) if len(values) > 1 else default


def short_hash(text: str, n: int = 8) -> str:
    """Hash court pour déduplication"""
    return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()[:n]


def timer(func):
    """Décorateur de profiling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = dt.datetime.now()
        result = func(*args, **kwargs)
        elapsed = (dt.datetime.now() - start).total_seconds() * 1000
        if elapsed > 100:
            LOGGER.debug(f"{func.__name__} pris {elapsed:.1f}ms")
        return result
    return wrapper