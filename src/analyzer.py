# Orchestration du pipeline complet : lecture → filtrage → appel LLM → validation → résultat structuré pour l'analyste.
# Ce module ne déclenche jamais d'action automatique (blocage, suppression,isolation) : il produit uniquement une analyse pour validation humaine.

import logging
from pathlib import Path

from src.llm_client import appeler_llm
from src.parser import filtrer_evenements_suspects
from src.validator import parser_et_valider

logger = logging.getLogger("ai_log_analyzer")

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "log_analysis.txt"


def charger_prompt_systeme(chemin: Path = PROMPT_PATH) -> str:
    with open(chemin, "r", encoding="utf-8") as f:
        return f.read()


def analyser_fichier(chemin_log: str) -> list[dict]:
# Analyse un fichier de logs et retourne une liste de résultats structurés (vide si aucun événement suspect ou si l'analyse échoue).
    logger.info(f"Analyse démarrée pour {chemin_log}")

    evenements = filtrer_evenements_suspects(chemin_log)
    logger.info(f"{len(evenements)} événement(s) suspect(s) détecté(s)")

    if not evenements:
        logger.info("Aucun événement suspect — aucune analyse LLM nécessaire")
        return []

    prompt_systeme = charger_prompt_systeme()
    log_regroupe = "\n".join(evenements)
    prompt_utilisateur = f"Analyse les logs suivants :\n{log_regroupe}"

    reponse = appeler_llm(prompt_utilisateur, prompt_systeme)
    if reponse is None:
        logger.error("Aucune réponse du LLM — analyse annulée")
        return []

    resultat = parser_et_valider(reponse, log_regroupe)
    if resultat is None:
        logger.error("Réponse LLM invalide après validation — analyse annulée")
        return []

    logger.info(f"Analyse terminée — sévérité : {resultat['severity']}")
    return [resultat]
