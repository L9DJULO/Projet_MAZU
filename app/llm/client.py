from __future__ import annotations

from app.config import get_settings


def generate_text(prompt: str, fallback: str) -> str:
    settings = get_settings()
    if settings.llm_mode == "ollama":
        return _generate_ollama(prompt, fallback)
    if settings.llm_mode == "gemini":
        return _generate_gemini(prompt, fallback)
    return fallback


def _generate_ollama(prompt: str, fallback: str) -> str:
    try:
        import httpx

        settings = get_settings()
        resp = httpx.post(
            f"{settings.ollama_host}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "").strip()
        return text or fallback
    except Exception:
        return fallback


def _generate_gemini(prompt: str, fallback: str) -> str:
    try:
        import httpx

        settings = get_settings()
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )
        resp = httpx.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text or fallback
    except Exception:
        return fallback
