"""Tests unitaires pour parser.py et validator.py.

Aucun appel réseau : ces tests s'exécutent sans clé API.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser import filtrer_evenements_suspects, lire_logs
from src.validator import (
    nettoyer_reponse_json,
    parser_et_valider,
    valider_schema,
    verifier_ioc_dans_source,
)

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


# ---------- parser.py ----------

def test_lire_logs_ignore_lignes_vides():
    lignes = list(lire_logs(str(SAMPLES_DIR / "auth.log")))
    assert all(ligne.strip() for ligne in lignes)
    assert len(lignes) > 0


def test_filtrer_evenements_suspects_detecte_bruteforce():
    evenements = filtrer_evenements_suspects(str(SAMPLES_DIR / "auth.log"))
    assert len(evenements) >= 10
    assert any("185.10.10.5" in e for e in evenements)


def test_filtrer_evenements_suspects_access_log_sans_anomalie():
    # access.log ne contient aucun motif suspect connu (SSH, firewall, chemins
    # web sensibles) -> aucune ligne ne doit être retenue.
    evenements = filtrer_evenements_suspects(str(SAMPLES_DIR / "access.log"))
    assert evenements == []


def test_filtrer_evenements_suspects_detecte_scan_firewall():
    evenements = filtrer_evenements_suspects(str(SAMPLES_DIR / "firewall.log"))
    assert len(evenements) == 8
    assert all("198.51.100.9" in e for e in evenements)


# ---------- validator.py ----------

def test_nettoyer_reponse_json_retire_balises_markdown():
    brut = '```json\n{"a": 1}\n```'
    assert nettoyer_reponse_json(brut) == '{"a": 1}'


def test_nettoyer_reponse_json_sans_balises():
    brut = '{"a": 1}'
    assert nettoyer_reponse_json(brut) == '{"a": 1}'


def _analyse_valide() -> dict:
    return {
        "summary": "Test",
        "severity": "high",
        "indicators": ["185.10.10.5"],
        "attack_hypothesis": "Brute force probable",
        "recommendations": ["Vérifier les logs"],
        "confidence": "medium",
    }


def test_valider_schema_accepte_analyse_complete():
    assert valider_schema(_analyse_valide()) is True


def test_valider_schema_rejette_champ_manquant():
    analyse = _analyse_valide()
    del analyse["severity"]
    assert valider_schema(analyse) is False


def test_valider_schema_rejette_severite_invalide():
    analyse = _analyse_valide()
    analyse["severity"] = "catastrophic"  # hors énumération autorisée
    assert valider_schema(analyse) is False


def test_verifier_ioc_dans_source_detecte_hallucination():
    analyse = _analyse_valide()
    analyse["indicators"] = ["185.10.10.5", "203.0.113.99"]  # 2e IP absente
    source = "log contenant uniquement 185.10.10.5"
    non_verifies = verifier_ioc_dans_source(analyse, source)
    assert non_verifies == ["203.0.113.99"]


def test_parser_et_valider_pipeline_complet():
    reponse_brute = json.dumps(_analyse_valide())
    source = "log contenant 185.10.10.5"
    resultat = parser_et_valider(reponse_brute, source)
    assert resultat is not None
    assert resultat["severity"] == "high"
    assert resultat["ioc_non_verifies"] == []


def test_parser_et_valider_rejette_json_invalide():
    resultat = parser_et_valider("ceci n'est pas du JSON", "peu importe")
    assert resultat is None
