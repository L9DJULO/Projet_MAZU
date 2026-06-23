from __future__ import annotations

from app.config import get_settings


def generate_text(prompt: str, fallback: str) -> str:
    settings = get_settings()
    if settings.llm_mode != "ollama":
        return fallback

    try:
        import httpx

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
