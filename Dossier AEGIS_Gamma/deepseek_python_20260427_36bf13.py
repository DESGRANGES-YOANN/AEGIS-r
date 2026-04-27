"""
AEGIS-Γ - Orchestrateur principal V4.0
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

from aegis_gamma.core.enums import ProfilEthique
from aegis_gamma.core.models import DecisionTraced, ZoneDeTension
from aegis_gamma.core.utils import CONFIG, LOGGER, now, clamp
from aegis_gamma.modules.cartographe import CartographeBrouillage
from aegis_gamma.modules.validateur import ValidateurTerrain
from aegis_gamma.modules.apprentissage import ApprentissageBrouillage
from aegis_gamma.modules.priorisation import PriorisationStrategique
from aegis_gamma.modules.persistance import GestionnairePersistance
from aegis_gamma.modules.visualiseur import VisualiseurCartographie
from aegis_gamma.modules.ethique import ControleurEthique
from aegis_gamma.modules.reseaux import AnalyseurReseaux
from aegis_gamma.modules.predicteur import PredicteurTemporel
from aegis_gamma.modules.simulateur import SimulateurStrategique
from aegis_gamma.modules.resilience import AnalyseurResilience
from aegis_gamma.modules.multilingue import AnalyseurMultilingue
from aegis_gamma.modules.coordination import DetecteurCoordination
from aegis_gamma.modules.optimiseur import OptimiseurAutoAdaptatif
from aegis_gamma.modules.expert import InterfaceSystemeExpert
from aegis_gamma.modules.credibilite import AnalyseurCredibilite
from aegis_gamma.modules.multimodal import AnalyseurMultimodal
from aegis_gamma.modules.argumentation import ArgumentationMiner
from aegis_gamma.modules.detecteur_ia import DetecteurAIGenerated
from aegis_gamma.modules.framing import NarrativeFramingAnalyzer
from aegis_gamma.modules.harm import HarmImpactAssessor
from aegis_gamma.modules.prebunking import PrebunkingEngine


class SystemeControleNarratifV4:
    """Système unifié intégrant tous les modules"""

    def __init__(self, nom: str = "AEGIS-Γ-V4", profil: ProfilEthique = ProfilEthique.INSTITUTIONNEL):
        self.nom = nom
        self.version = "4.0.0"

        # Modules de base
        self.cartographe = CartographeBrouillage(nom)
        self.validateur = ValidateurTerrain(self.cartographe)
        self.apprentissage = ApprentissageBrouillage()
        self.priorisation = PriorisationStrategique()
        self.persistance = GestionnairePersistance()
        self.visualiseur = VisualiseurCartographie()
        self.controle_ethique = ControleurEthique(profil)
        self.analyseur_reseaux = AnalyseurReseaux()

        # Modules avancés
        self.predicteur = PredicteurTemporel()
        self.simulateur = SimulateurStrategique(seed=CONFIG.seed)
        self.analyseur_resilience = AnalyseurResilience()
        self.analyseur_multilingue = AnalyseurMultilingue()
        self.detecteur_coordination = DetecteurCoordination()
        self.optimiseur = OptimiseurAutoAdaptatif(seed=CONFIG.seed)
        self.expert = InterfaceSystemeExpert()
        self.credibilite = AnalyseurCredibilite(seed=CONFIG.seed)

        # Nouveaux modules V4
        self.multimodal = AnalyseurMultimodal()
        self.argumentation = ArgumentationMiner()
        self.detecteur_ia = DetecteurAIGenerated()
        self.framing = NarrativeFramingAnalyzer()
        self.harm = HarmImpactAssessor()
        self.prebunking = PrebunkingEngine()

        self.journal_decisions = []

        LOGGER.info(f"🚀 {self.nom} v{self.version} initialisé - 22 modules actifs")

    async def executer_cycle_complet_async(self, sujet: str, fragments: List[Tuple[str, str, float]]) -> Dict[str, Any]:
        LOGGER.info(f"Analyse du sujet: {sujet}")

        for type_src, contenu, charge in fragments[:CONFIG.max_fragments_par_sujet]:
            self.cartographe.ingerer_fragment(sujet, type_src, contenu, charge)

        zone = self.cartographe.analyser_sujet(sujet, recalculer=True)
        if not zone:
            return {"erreur": f"Aucune zone pour {sujet}"}

        frags_sujet = [f for f in self.cartographe.fragments.values() if f.sujet == sujet]

        # Analyses parallèles
        cred_analysis = await self.credibilite.analyser_credibilite_async(frags_sujet[0]) if frags_sujet else {}
        multimodal_analysis = await self.multimodal.analyser(frags_sujet[0]) if frags_sujet else {}
        arg_analysis = self.argumentation.analyser(frags_sujet[0].contenu) if frags_sujet else {}
        ia_analysis = self.detecteur_ia.analyser(frags_sujet[0]) if frags_sujet else {}
        framing_analysis = self.framing.analyser(zone, frags_sujet)
        validation = self.validateur.tester_hypothese_nulle(zone)
        ordre = self.priorisation.generer_ordre_investigation(list(self.cartographe.zones_tension.values()))
        prediction = self.predicteur.predire_evolution_zone(zone, list(zone.historique_tension))
        impact = self.harm.evaluer(zone)
        prebunking = self.prebunking.generer(zone, arg_analysis.get("fallacies_detectees", []))
        resilience = self.analyseur_resilience.analyser_resilience_profonde(zone, frags_sujet)

        score_confiance = self._calculer_score_confiance(zone, validation, cred_analysis, ia_analysis)
        decision = {
            "decision_id": f"DEC_{now().strftime('%Y%m%d%H%M%S')}_{sujet[:8]}",
            "sujet": sujet,
            "zone_tension": zone.to_dict(),
            "score_confiance": score_confiance,
            "validation": validation,
            "credibilite": cred_analysis,
            "ia_detection": ia_analysis,
            "argumentation": arg_analysis,
            "framing": framing_analysis,
            "multimodal": multimodal_analysis,
            "prediction": prediction,
            "impact": impact,
            "resilience": resilience,
            "prebunking": prebunking,
            "prochaines_actions": self._determiner_actions(zone, ordre)
        }

        audit = self.controle_ethique.auditer_decision(decision, {"sujet": sujet})

        self.journal_decisions.append(DecisionTraced(
            id=decision["decision_id"], date=now(), sujet=sujet, zone_id=zone.id,
            niveau_alerte=zone.niveau_alerte, score_confiance=score_confiance,
            version_regles=self.version
        ))

        return {
            "decision_id": decision["decision_id"],
            "sujet": sujet,
            "zone_tension": zone.to_dict(),
            "score_confiance": score_confiance,
            "validation": validation,
            "credibilite": cred_analysis,
            "ia_detection": ia_analysis,
            "argumentation": arg_analysis,
            "framing": framing_analysis,
            "multimodal": multimodal_analysis,
            "prediction": prediction,
            "impact": impact,
            "resilience": resilience,
            "prebunking": prebunking,
            "audit_ethique": audit,
            "prochaines_actions": decision["prochaines_actions"],
            "version": self.version
        }

    def _calculer_score_confiance(self, zone: ZoneDeTension, validation: Dict,
                                  cred_analysis: Dict, ia_analysis: Dict) -> float:
        score = zone.niveau_alerte * 0.3
        score += (validation.get("confiance_validation", 0.0) / 100.0) * 10.0 * 0.25
        score += min(2.0, len(zone.fragments_ids) * 0.05)

        if cred_analysis.get("score_credibilite_global", 0.5) < 0.4:
            score *= 0.8
        if ia_analysis.get("score_generation_ia", 0) > 0.7:
            score *= 0.7

        return clamp(score, 0.0, 10.0)

    def _determiner_actions(self, zone: ZoneDeTension, ordre: List) -> List[str]:
        pos = next((i for i, item in enumerate(ordre) if item["zone"].id == zone.id), -1)

        if pos == 0:
            return [f"🔴 Enquête prioritaire sur '{zone.sujet}'",
                    "Cartographier les acteurs et canaux",
                    "Surveillance en temps réel"]
        if pos < 3:
            return [f"🟠 Enquête préliminaire sur '{zone.sujet}'",
                    "Identifier les sources primaires",
                    "Préparer une contre-narrative"]
        return [f"🟡 Surveillance de '{zone.sujet}'",
                "Veille périodique",
                "Documenter les évolutions"]

    def executer_cycle_complet(self, sujet: str, fragments: List[Tuple[str, str, float]]) -> Dict[str, Any]:
        try:
            return asyncio.run(self.executer_cycle_complet_async(sujet, fragments))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.executer_cycle_complet_async(sujet, fragments))

    def sauvegarder(self, nom: Optional[str] = None) -> str:
        return str(self.persistance.sauvegarder_etat(self, nom))

    def visualiser(self):
        return self.visualiseur.generer_carte_thermique(list(self.cartographe.zones_tension.values()))