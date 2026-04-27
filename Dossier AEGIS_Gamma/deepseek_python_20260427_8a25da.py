"""
AEGIS-Γ - Interface en ligne de commande
"""

import argparse
import asyncio
import logging

from aegis_gamma.core.enums import ProfilEthique
from aegis_gamma.core.utils import CONFIG
from aegis_gamma.orchestrator.systeme import SystemeControleNarratifV4


async def demo_complete():
    print("\n" + "=" * 80)
    print("🚀 AEGIS-Γ V4.0 - DÉMONSTRATION COMPLÈTE")
    print("=" * 80)

    systeme = SystemeControleNarratifV4(nom="AEGIS-DEMO", profil=ProfilEthique.CITOYEN)

    sujet = "vaccins_covid"
    fragments = [
        ("article_presse", "Nouvelle étude sur l'efficacité des vaccins #Science", 5.0),
        ("theorie_alternative", "Les vaccins modifient l'ADN selon des sources anonymes", 8.5),
        ("meme", "Mon 5G après le vaccin 📡 #Vaccin", 7.0),
        ("post_reseau_social", "Mon cousin a eu des effets secondaires graves!", 9.0),
        ("rapport_officiel", "Rapport OMS sur la sécurité vaccinale. Selon l'OMS, l'étude confirme.", 4.0),
    ]

    resultat = await systeme.executer_cycle_complet_async(sujet, fragments)

    print(f"\n📊 RÉSULTATS DE L'ANALYSE:")
    print(f"   Décision ID    : {resultat['decision_id']}")
    print(f"   Niveau alerte  : {resultat['zone_tension']['niveau_alerte']:.1f}/10")
    print(f"   Score confiance: {resultat['score_confiance']:.1f}/10")

    if resultat.get('credibilite', {}).get('score_credibilite_global'):
        print(f"   Crédibilité    : {resultat['credibilite']['score_credibilite_global']:.0%}")
    if resultat.get('ia_detection', {}).get('score_generation_ia'):
        print(f"   Détection IA   : {resultat['ia_detection']['score_generation_ia']:.0%}")
    if resultat.get('prediction', {}).get('tendance_actuelle', {}).get('direction'):
        print(f"   Tendance prédite: {resultat['prediction']['tendance_actuelle']['direction']}")
    if resultat.get('impact', {}).get('niveau'):
        print(f"   Impact estimé   : {resultat['impact']['niveau']} ({resultat['impact']['impact_total']:.0%})")
    if resultat.get('argumentation', {}).get('fallacies_detectees'):
        print(f"   Fallacies       : {', '.join(resultat['argumentation']['fallacies_detectees'])}")

    print(f"\n🎯 ACTIONS RECOMMANDÉES:")
    for action in resultat['prochaines_actions']:
        print(f"   • {action}")

    if resultat.get('prebunking', {}).get('recommandation'):
        print(f"\n🛡️ PRÉ-BUNKAGE: {resultat['prebunking']['recommandation']}")

    print(f"\n✅ Démonstration terminée")
    print("=" * 80)

    return systeme


def main():
    parser = argparse.ArgumentParser(description="AEGIS-Γ V4.0 - Système de contrôle narratif")
    parser.add_argument("--demo", action="store_true", help="Lancer la démonstration complète")
    parser.add_argument("--verbose", action="store_true", help="Logs détaillés")
    args = parser.parse_args()

    if args.verbose:
        CONFIG.verbose = True
        logging.getLogger().setLevel(logging.DEBUG)

    if args.demo:
        asyncio.run(demo_complete())
    else:
        print(__doc__)


if __name__ == "__main__":
    main()