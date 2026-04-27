from aegis_gamma import SystemeControleNarratifV4
from aegis_gamma.core.enums import ProfilEthique

systeme = SystemeControleNarratifV4(profil=ProfilEthique.CITOYEN)

fragments = [
    ("article_presse", "Nouvelle étude sur l'efficacité des vaccins", 5.0),
    ("theorie_alternative", "Les vaccins modifient l'ADN", 8.5),
]

rapport = systeme.executer_cycle_complet("vaccins", fragments)
print(f"Niveau alerte: {rapport['zone_tension']['niveau_alerte']}")