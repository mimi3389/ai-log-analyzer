# Chargement de la configuration (variables d'environnement) et du logging.
# Aucun secret n'est jamais codé en dur ici : tout provient de l'environnement,
# chargé depuis un fichier .env (voir .env.example) via python-dotenv.

import logging
import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-5"
LOG_FILE = "ai_log_analyzer.log"


def get_api_key() -> str:
    # Retourne la clé API LLM, ou lève une erreur explicite si absente.
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise EnvironmentError(
            "LLM_API_KEY manquant. Copiez .env.example en .env et renseignez "
            "votre clé API avant de lancer le script."
        )
    return key


def get_model() -> str:
    return os.getenv("LLM_MODEL", DEFAULT_MODEL)


def get_api_url() -> str:
    return os.getenv("LLM_API_URL", DEFAULT_API_URL)


def configurer_logging() -> logging.Logger:
# Configure un logger applicatif écrivant en console et dans un fichier.
# Ne jamais logger de secrets (clés API, tokens) ni le contenu complet des headers HTTP.

    logger = logging.getLogger("ai_log_analyzer")
    if logger.handlers:
        # Évite les handlers dupliqués si configurer_logging() est appelé
        # plusieurs fois (ex : tests).
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    fichier = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fichier.setFormatter(formatter)
    logger.addHandler(fichier)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger
