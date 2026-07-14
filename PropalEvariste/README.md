## Démarrage

```bash
pip install -r requirements.txt
python app.py
```

Ensuite ouvre `http://localhost:3000`.

## Variables d'environnement

- `PORT`: port du serveur, par défaut `3000`
- `HOST`: adresse d'écoute, par défaut `127.0.0.1`
- `LOCAL_MODEL_BASE_URL`: base URL du service Custom Vision local, par défaut `http://127.0.0.1:80`
- `AUTOGEN_MODEL`: modèle utilisé pour la recommandation multi-agents, par défaut `llama3.2:latest`
- `AUTOGEN_BASE_URL`: base URL OpenAI-compatible du serveur LLM local, par défaut `http://127.0.0.1:11434/v1`
- `AUTOGEN_API_KEY`: clé API factice pour le serveur local, par défaut `ollama`
- `AUTOGEN_TEMPERATURE`: température de génération pour la recommandation, par défaut `0.5`

## Fonctionnement

- `/api/image` relaie les requêtes image vers `LOCAL_MODEL_BASE_URL/image`
- `/api/url` relaie les requêtes URL vers `LOCAL_MODEL_BASE_URL/url`
- `/api/vehicle-report` renvoie aussi une recommandation atelier générée par un groupe d'agents AutoGen à partir du dossier véhicule et du prix estimé
- L'interface front reste côté navigateur pour le mode Azure Cloud