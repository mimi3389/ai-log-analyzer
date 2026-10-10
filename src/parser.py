"""Lecture de fichiers de logs et pré-filtrage par expressions régulières.

Les lignes sont lues en flux (générateur) pour rester utilisable sur des
fichiers volumineux sans charger l'intégralité en mémoire.
"""

import re
from collections.abc import Iterator

# Motifs de pré-filtrage : n'étendre cette liste qu'avec des motifs réellement pertinents pour un SOC (réduit le bruit envoyé au LLM).
PATTERN_SSH_FAILED = re.compile(
    r"(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>[\d:]+).*"
    r"Failed password for (?:invalid user )?(?P<user>\S+) "
    r"from (?P<ip>[\d.]+) port (?P<port>\d+)"
)
PATTERN_SSH_ACCEPTED = re.compile(
    r"(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>[\d:]+).*"
    r"Accepted password for (?P<user>\S+) from (?P<ip>[\d.]+) port (?P<port>\d+)"
)
PATTERN_FIREWALL_DENY = re.compile(
    r"SRC=(?P<src>[\d.]+)\s+DST=(?P<dst>[\d.]+).*DPT=(?P<port>\d+)"
)
PATTERN_HTTP_SUSPECT = re.compile(
    r'"(?:GET|POST)\s+/(?:wp-login\.php|admin|\.env|phpmyadmin)\S*\s+HTTP'
)

PATTERNS_SUSPECTS = [
    PATTERN_SSH_FAILED,
    PATTERN_SSH_ACCEPTED,
    PATTERN_FIREWALL_DENY,
    PATTERN_HTTP_SUSPECT,
]


def lire_logs(chemin: str) -> Iterator[str]:
    # Lit un fichier ligne par ligne (générateur, faible empreinte mémoire).
    with open(chemin, "r", encoding="utf-8", errors="ignore") as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne:
                yield ligne


def filtrer_evenements_suspects(chemin: str) -> list[str]:
    # Ne conserve que les lignes correspondant à un motif d'intérêt SOC.
    resultats = []
    for ligne in lire_logs(chemin):
        if any(pattern.search(ligne) for pattern in PATTERNS_SUSPECTS):
            resultats.append(ligne)
    return resultats
