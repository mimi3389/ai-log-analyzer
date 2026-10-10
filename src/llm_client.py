"""Client API LLM robuste : timeout explicite, retry avec backoff exponentiel,
gestion différenciée des erreurs réseau / HTTP / rate limit.

Écrit par défaut pour l'API Anthropic (/v1/messages). Pour adapter à un
autre fournisseur compatible, seule cette fonction nécessite des changements
(URL, headers, format du payload, extraction de la réponse) — le reste du
pipeline n'en dépend jamais directement.
"""

import logging
import time

import requests

from src.config import get_api_key, get_api_url, get_model

logger = logging.getLogger("ai_log_analyzer")

MAX_TOKENS = 1000
TIMEOUT_SECONDES = 30


def appeler_llm(
    prompt_utilisateur: str,
    prompt_systeme: str,
    max_tentatives: int = 3,
) -> str | None:
    # Appelle l'API LLM avec retry/backoff. Retourne le texte généré, ou None en cas d'échec définitif (jamais d'exception non gérée).
    headers = {
        "x-api-key": get_api_key(),
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": get_model(),
        "max_tokens": MAX_TOKENS,
        "system": prompt_systeme,
        "messages": [{"role": "user", "content": prompt_utilisateur}],
    }

    delai = 1
    for tentative in range(1, max_tentatives + 1):
        try:
            r = requests.post(
                get_api_url(),
                headers=headers,
                json=payload,
                timeout=TIMEOUT_SECONDES,
            )
            r.raise_for_status()
            data = r.json()
            return data["content"][0]["text"]

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response is not None else None
            if code == 429:
                logger.warning(
                    f"Rate limit atteint (tentative {tentative}/{max_tentatives}), "
                    f"attente {delai}s"
                )
                time.sleep(delai)
                delai *= 2
            elif code is not None and code >= 500:
                logger.warning(
                    f"Erreur serveur {code} (tentative {tentative}/{max_tentatives}), "
                    f"attente {delai}s"
                )
                time.sleep(delai)
                delai *= 2
            else:
                logger.error(f"Erreur HTTP non récupérable ({code}) : {e}")
                return None

        except requests.exceptions.Timeout:
            logger.warning(
                f"Timeout dépassé (tentative {tentative}/{max_tentatives})"
            )
            time.sleep(delai)
            delai *= 2

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau : {e}")
            time.sleep(delai)
            delai *= 2

    logger.error("Échec de l'appel LLM après toutes les tentatives")
    return None
