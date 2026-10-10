#Validation de la sortie JSON du LLM et vérification anti-hallucination.
#Ne jamais faire confiance à une sortie LLM, même "structurée" : on valide
#systématiquement présence des champs, types, et valeurs autorisées avant
#toute utilisation en aval.

import json
import logging

logger = logging.getLogger("ai_log_analyzer")

CHAMPS_REQUIS = {
    "summary",
    "severity",
    "indicators",
    "attack_hypothesis",
    "recommendations",
    "confidence",
}
SEVERITES_VALIDES = {"low", "medium", "high", "critical"}
CONFIANCES_VALIDES = {"low", "medium", "high"}


def nettoyer_reponse_json(texte: str) -> str:
    # Retire d'éventuelles balises Markdown résiduelles (```json ... ```)avant tentative de parsing JSON.
    texte = texte.strip()
    if texte.startswith("```"):
        parties = texte.split("```")
        if len(parties) > 1:
            texte = parties[1]
            if texte.startswith("json"):
                texte = texte[4:]
            texte = texte.strip()
    return texte


def valider_schema(data: dict) -> bool:
    # Vérifie présence des champs requis, et validité des énumérations.
    if not isinstance(data, dict):
        return False
    if not CHAMPS_REQUIS.issubset(data.keys()):
        logger.warning(f"Champs manquants : {CHAMPS_REQUIS - data.keys()}")
        return False
    if data["severity"] not in SEVERITES_VALIDES:
        logger.warning(f"Sévérité invalide : {data['severity']}")
        return False
    if data["confidence"] not in CONFIANCES_VALIDES:
        logger.warning(f"Confiance invalide : {data['confidence']}")
        return False
    if not isinstance(data["indicators"], list):
        return False
    if not isinstance(data["recommendations"], list):
        return False
    return True


def verifier_ioc_dans_source(analyse: dict, log_source: str) -> list[str]:
    # Retourne les IOC mentionnés par le LLM mais absents du texte source(détection d'hallucination par comparaison programmatique).
    return [
        ioc for ioc in analyse.get("indicators", []) if str(ioc) not in log_source
    ]


def parser_et_valider(reponse_brute: str, log_source: str) -> dict | None:
    # Pipeline complet : nettoyage → parsing → validation de schéma→ vérification anti-hallucination. Retourne None si invalide.
    try:
        data = json.loads(nettoyer_reponse_json(reponse_brute))
    except json.JSONDecodeError:
        logger.warning("Réponse LLM non parsable en JSON")
        return None

    if not valider_schema(data):
        return None

    ioc_suspects = verifier_ioc_dans_source(data, log_source)
    if ioc_suspects:
        data["ioc_non_verifies"] = ioc_suspects
        logger.warning(f"IOC non vérifiés dans la source : {ioc_suspects}")
    else:
        data["ioc_non_verifies"] = []

    return data
