from __future__ import annotations

import os
from typing import Any

from autogen import AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent
import requests
from flask import Flask, Response, jsonify, render_template, request


PORT = int(os.getenv("PORT", "3000"))
HOST = os.getenv("HOST", "127.0.0.1")
LOCAL_MODEL_BASE_URL = os.getenv("LOCAL_MODEL_BASE_URL", "http://127.0.0.1:80")
AUTOGEN_MODEL = os.getenv("AUTOGEN_MODEL", "llama3.2:latest")
AUTOGEN_BASE_URL = os.getenv("AUTOGEN_BASE_URL", "http://127.0.0.1:11434/v1")
AUTOGEN_API_KEY = os.getenv("AUTOGEN_API_KEY", "ollama")
AUTOGEN_TEMPERATURE = float(os.getenv("AUTOGEN_TEMPERATURE", "0.5"))

app = Flask(__name__, static_url_path="")

def with_cors(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Prediction-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.after_request
def add_cors_headers(response: Response) -> Response:
    return with_cors(response)


@app.get("/")
def index() -> str:
    return render_template("index.html")


def build_llm_config() -> dict[str, Any]:
    return {
        "config_list": [
            {
                "model": AUTOGEN_MODEL,
                "base_url": AUTOGEN_BASE_URL,
                "api_key": AUTOGEN_API_KEY,
                "price": [0, 0],
            }
        ],
        "temperature": AUTOGEN_TEMPERATURE,
    }


def format_vehicle_summary(payload: dict[str, Any]) -> str:
    vision_result = payload.get("vision_result") or {}
    condition = payload.get("etat_estime") or {}
    vehicle = payload.get("vehicule") or {}

    return (
        "Dossier véhicule:\n"
        f"- Modèle: {vehicle.get('modele', 'Inconnu')}\n"
        f"- Année: {vehicle.get('annee', 'Inconnue')}\n"
        f"- Kilométrage: {vehicle.get('kilometrage_km', 'Inconnu')} km\n"
        f"- Carburant: {vehicle.get('carburant', 'Inconnu')}\n"
        f"- Propriétaires: {vehicle.get('nb_proprietaires', 'Inconnu')}\n"
        f"- Prix d'achat neuf: {vehicle.get('cout_achat_neuf_eur', 'Inconnu')} €\n"
        f"- Prix estimé: {payload.get('estimated_price_eur', 'Inconnu')} €\n"
        f"- Vision: {condition.get('label', 'Inconnue')} ({condition.get('confidence', 'n/a')})\n"
        f"- Détail vision: {vision_result}"
    )


def generate_mechanic_recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    llm_config = build_llm_config()

    researcher = AssistantAgent(
        name="ResearcherAgent",
        llm_config=llm_config,
        system_message=(
            "Tu es un mécanicien expert et un analyste automobile. "
            "Analyse les informations du véhicule, identifie les risques techniques, "
            "les points de contrôle prioritaires et les éléments cohérents avec le carburant, "
            "le kilométrage, l'année et le prix estimé. "
            "Réponds en français, de façon concise et factuelle. "
            "À la fin, écris 'RESEARCH COMPLETE'."
        ),
    )

    summarizer = AssistantAgent(
        name="SummarizerAgent",
        llm_config=llm_config,
        system_message=(
            "Tu es un synthétiseur pour atelier mécanique. "
            "Transforme l'analyse technique en recommandation concrète pour le mécanicien qui vient d'acheter la voiture. "
            "Inclue: verdict global, réparations à prioriser, contrôles à faire immédiatement, "
            "et si l'achat paraît cohérent par rapport au prix estimé. "
            "Réponds en français avec des phrases courtes et termine par 'TERMINATE'."
        ),
    )

    planner = UserProxyAgent(
        name="Planner",
        human_input_mode="NEVER",
        llm_config=llm_config,
        system_message=(
            "Tu coordonnes le diagnostic multi-agents. "
            "Lis le dossier véhicule, demande d'abord une analyse au researcher, puis une synthèse au summarizer. "
            "Quand la recommandation finale est claire, termine avec 'TERMINATE'."
        ),
        code_execution_config=False,
        is_termination_msg=lambda message: message.get("content", "").strip().endswith("TERMINATE"),
    )

    groupchat = GroupChat(
        agents=[planner, researcher, summarizer],
        messages=[],
        max_round=4,
        speaker_selection_method="auto",
    )

    manager = GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config,
    )

    chat_result = planner.initiate_chat(
        manager,
        message=(
            "Tu dois recommander le meilleur plan d'action au mécanicien qui vient d'acheter cette voiture.\n"
            f"{format_vehicle_summary(payload)}\n\n"
            "Rends une recommandation pratique et actionnable."
        ),
    )

    print(chat_result.chat_history)

    summary = getattr(chat_result, "summary", None)
    if isinstance(summary, str) and summary.strip():
        recommendation = summary.replace("TERMINATE", "").strip()
    else:
        chat_history = getattr(chat_result, "chat_history", None) or []
        if chat_history:
            last_message = chat_history[-1].get("content", "")
            recommendation = str(last_message).replace("TERMINATE", "").strip()
        else:
            recommendation = "Aucune recommandation n'a pu être générée."

    return {
        "recommendation": recommendation,
        "transcript": serialize_chat_history(getattr(chat_result, "chat_history", None) or []),
    }


def serialize_chat_history(chat_history: list[dict[str, Any]]) -> list[dict[str, str]]:
    transcript: list[dict[str, str]] = []

    for message in chat_history:
        speaker = str(message.get("name") or message.get("role") or "Agent")
        content = message.get("content", "")
        if isinstance(content, dict):
            content = str(content)
        transcript.append(
            {
                "speaker": speaker,
                "content": str(content).replace("TERMINATE", "").strip(),
            }
        )

    return transcript


def proxy_prediction(target_path: str):
    if request.method == "OPTIONS":
        return ("", 204)

    body = request.get_data()
    target = f"{LOCAL_MODEL_BASE_URL.rstrip('/')}{target_path}"
    headers = {
        "Content-Type": request.headers.get("Content-Type", "application/octet-stream"),
    }

    prediction_key = request.headers.get("Prediction-Key")
    if prediction_key:
        headers["Prediction-Key"] = prediction_key

    try:
        upstream_response = requests.post(target, data=body, headers=headers, timeout=60)
    except requests.RequestException as error:
        return (
            jsonify(
                error="Proxy request failed",
                message=(
                    f"Impossible de joindre le modèle local à {LOCAL_MODEL_BASE_URL}. "
                    "Vérifie que le conteneur Custom Vision est démarré et qu'il expose bien le port 80. "
                    f"Erreur réseau: {error}"
                ),
                target=LOCAL_MODEL_BASE_URL,
            ),
            502,
        )

    response = Response(
        upstream_response.content,
        status=upstream_response.status_code,
        content_type=upstream_response.headers.get("Content-Type", "application/octet-stream"),
    )
    content_length = upstream_response.headers.get("Content-Length")
    if content_length:
        response.headers["Content-Length"] = content_length
    return response


@app.route("/api/image", methods=["POST", "OPTIONS"])
def api_image():
    return proxy_prediction("/image")


@app.route("/api/url", methods=["POST", "OPTIONS"])
def api_url():
    return proxy_prediction("/url")


@app.route("/api/vehicle-report", methods=["POST", "OPTIONS"])
def api_vehicle_report():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Invalid payload", message="Le corps JSON est manquant ou invalide."), 400

    try:
        report = generate_mechanic_recommendation(payload)
    except Exception as error:
        return (
            jsonify(
                error="Recommendation generation failed",
                message=(
                    "Le système multi-agents n'a pas pu générer la recommandation. "
                    "Vérifie que le serveur LLM local est accessible. "
                    f"Erreur: {error}"
                ),
                dossier=payload,
            ),
            502,
        )
    
    recommendation = "J'ai bien peur qu'il n'y ai plus rien à faire 😔" if report["recommendation"] == "" else report["recommendation"]

    return jsonify(
        received=True,
        message="Dossier véhicule reçu.",
        dossier=payload,
        recommendation=recommendation,
        transcript=report["transcript"],
    )


def main() -> None:
    app.run(host=HOST, port=PORT, debug=False)


if __name__ == "__main__":
    main()