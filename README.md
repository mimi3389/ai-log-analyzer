# AI Log Analyzer

Outil en ligne de commande qui lit un fichier de logs de sécurité, pré-filtre les événements suspects (regex), interroge un LLM avec un prompt système strict, valide la sortie JSON, et produit une analyse structurée destinée à la **validation d'un analyste humain**.

## Principe directeur

```
Detection → AI Analysis → Recommendation → Human Validation → Response
```

Ce script **n'exécute jamais** d'action automatique (blocage, suppression, isolation). Il produit uniquement une analyse structurée pour un analyste SOC.

## Architecture

```
Log file → Parsing regex → Sélection des événements pertinents
        → Appel LLM robuste (prompt système strict)
        → Validation du schéma JSON
        → Vérification anti-hallucination (IOC comparés à la source)
        → Résultat structuré pour l'analyste
```

```
ai-log-analyzer/
├── main.py                  # point d'entrée CLI
├── requirements.txt
├── .env.example              # modèle de configuration (copier en .env)
├── .gitignore
├── src/
│   ├── config.py              # chargement env + logging
│   ├── parser.py               # lecture fichier + regex de pré-filtrage
│   ├── llm_client.py            # appel API LLM robuste (retry, backoff, timeout)
│   ├── validator.py             # validation JSON + anti-hallucination
│   └── analyzer.py              # orchestration du pipeline
├── prompts/
│   └── log_analysis.txt          # prompt système (jamais codé en dur dans le code)
├── samples/
│   ├── auth.log                  # exemple : brute force SSH
│   ├── access.log                # exemple : trafic web sans anomalie
│   └── firewall.log              # exemple : scan de ports
└── tests/
    └── test_parser_validator.py   # tests unitaires (sans appel API)
```

## Installation

```bash
git clone <votre-repo> ai-log-analyzer
cd ai-log-analyzer

python3 -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# puis éditez .env et renseignez votre clé API
```

## Configuration (`.env`)

```dotenv
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=claude-sonnet-4-5
LLM_API_URL=https://api.anthropic.com/v1/messages
```

Le client est écrit pour l'API Anthropic (format `/v1/messages`) par défaut, mais `src/llm_client.py` est volontairement isolé du reste du pipeline : pour utiliser un autre fournisseur compatible, il suffit d'adapter cette seule fonction (URL, headers, format du payload et extraction de la réponse).

**Ne commitez jamais votre fichier `.env`** — il est déjà exclu via `.gitignore`.

## Utilisation

```bash
python main.py samples/auth.log
```

Sortie (exemple) :

```json
{
  "summary": "Multiples échecs d'authentification SSH depuis une IP unique, suivis d'un succès.",
  "severity": "high",
  "indicators": ["185.10.10.5", "admin", "root"],
  "attack_hypothesis": "Tentative de brute force SSH, potentiellement suivie d'une compromission.",
  "recommendations": [
    "Vérifier la légitimité de la connexion de jdupont depuis 10.0.0.12",
    "Bloquer temporairement 185.10.10.5 après validation humaine"
  ],
  "confidence": "medium"
}
```

Si aucun événement suspect n'est détecté dans le fichier (ex : `samples/access.log`), aucun appel LLM n'est effectué et le script l'indique clairement — pas de coût ni de bruit inutiles.

## Tests

Les tests unitaires couvrent le parsing regex et la validation JSON (aucun appel réseau, donc exécutables sans clé API) :

```bash
pip install pytest
pytest tests/ -v
```

## Logs applicatifs

Chaque exécution écrit dans `ai_log_analyzer.log` (créé automatiquement, exclu du contrôle de version). Aucun secret n'y est jamais écrit.

## Garde-fous de sécurité

- Clé API chargée uniquement via variable d'environnement (`.env`, jamais en dur)
- Timeout explicite sur tout appel réseau + retry avec backoff exponentiel sur erreurs transitoires (429, 500)
- Validation stricte du schéma JSON retourné par le LLM avant tout usage
- Vérification programmatique de chaque IOC mentionné par le modèle contre le texte source (détection d'hallucination)
- Aucune action destructive ou automatique : seule une analyse pour validation humaine est produite

## Licence

Projet pédagogique — libre d'utilisation et d'adaptation dans le cadre de votre propre apprentissage ou laboratoire.
