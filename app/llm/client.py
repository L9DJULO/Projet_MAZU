from __future__ import annotations

import re

from app.config import get_settings


def generate_text(prompt: str, fallback: str) -> str:
    settings = get_settings()
    if settings.llm_mode == "ollama":
        return _generate_ollama(prompt, fallback)
    if settings.llm_mode == "gemini":
        return _generate_gemini(prompt, fallback)
    if settings.llm_mode == "mistral":
        return _generate_mistral(prompt, fallback)
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


def _generate_mistral(prompt: str, fallback: str) -> str:
    try:
        import httpx

        settings = get_settings()
        resp = httpx.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.mistral_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.mistral_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.4,
            },
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        return _clean(text) or fallback
    except Exception:
        return fallback


_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF←-⟿⬀-⯿]",
    flags=re.UNICODE,
)


def _clean(text: str) -> str:
    """Sortie carree : pas d'emoji, pas de markdown, pas de guillemets parasites."""
    text = _EMOJI.sub("", text)
    text = text.replace("**", "").replace("__", "").replace("##", "").replace("`", "")
    text = "\n".join(line.strip() for line in text.splitlines())
    return text.strip().strip('"').strip()


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
