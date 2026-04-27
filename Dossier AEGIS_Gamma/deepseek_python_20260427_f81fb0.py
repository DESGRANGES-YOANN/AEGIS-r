"""
AEGIS-Γ - Énumérations centrales
"""

from enum import Enum


class TypeSource(Enum):
    RAPPORT_OFFICIEL = "rapport_officiel"
    THEORIE_ALTERNATIVE = "theorie_alternative"
    ARTICLE_PRESSE = "article_presse"
    MEME = "meme"
    RAPPORT_TECHNIQUE = "rapport_technique"
    OEUVRE_FICTION = "oeuvre_fiction"
    TEMOIGNAGE = "temoignage"
    DOCUMENT_HISTORIQUE = "document_historique"
    POST_RESEAU_SOCIAL = "post_reseau_social"


class TypeOpacite(Enum):
    COMPLEXITE_TECHNIQUE = "complexite_technique"
    SURCHARGE_THEORIQUE = "surcharge_theorique"
    PARADOXE_TEMPOREL = "paradoxe_temporel"
    CONTRADICTION_LOGISTIQUE = "contradiction_logistique"
    ABSENCE_SOURCE = "absence_source"
    PROPAGATION_MEMETIQUE = "propagation_memetique"
    JARGON_EXCESSIF = "jargon_excessif"
    ANECDOTISATION = "anecdotisation"


class TypeTension(Enum):
    EMOTIONNELLE = "emotionnelle"
    COGNITIVE = "cognitive"
    SOCIALE = "sociale"
    INSTITUTIONNELLE = "institutionnelle"


class ProfilEthique(Enum):
    CITOYEN = "citoyen"
    JOURNALISTIQUE = "journalistique"
    INSTITUTIONNEL = "institutionnel"
    RECHERCHE = "recherche"


class TypeSourceCredibilite(Enum):
    OFFICIEL_VERIFIE = "officiel_verifie"
    OFFICIEL_NON_VERIFIE = "officiel_non_verifie"
    PRESSE_RECOMMANDEE = "presse_recommandee"
    PRESSE_AUTRE = "presse_autre"
    ACADEMIQUE = "academique"
    RESEAU_SOCIAL_VERIFIE = "reseau_social_verifie"
    RESEAU_SOCIAL_ANONYME = "reseau_social_anonyme"
    BLOG_PERSONNEL = "blog_personnel"
    INCONNU = "inconnu"


# Lookup tables O(1)
_TYPE_SOURCE_LOOKUP = {t.value: t for t in TypeSource}
_TYPE_OPACITE_LOOKUP = {t.value: t for t in TypeOpacite}
_TYPE_TENSION_LOOKUP = {t.value: t for t in TypeTension}
_PROFIL_LOOKUP = {p.value: p for p in ProfilEthique}