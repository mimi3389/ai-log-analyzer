#!/usr/bin/env python3
"""AI Log Analyzer — point d'entrée CLI.

Usage :
    python main.py <chemin_vers_fichier_log>

Produit une analyse structurée (JSON) pour validation par un analyste SOC.
Ne déclenche jamais d'action automatique.
"""

import json
import sys

from src.analyzer import analyser_fichier
from src.config import configurer_logging


def main() -> int:
    configurer_logging()

    if len(sys.argv) < 2:
        print("Usage : python main.py <chemin_vers_fichier_log>")
        return 1

    chemin_log = sys.argv[1]
    resultats = analyser_fichier(chemin_log)

    if not resultats:
        print("Aucune analyse produite (pas d'événement suspect ou échec — voir ai_log_analyzer.log).")
        return 0

    for resultat in resultats:
        print(json.dumps(resultat, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
