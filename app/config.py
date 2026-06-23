from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_mode: Literal["mock", "real"] = "mock"

    azure_vision_endpoint: str = ""
    azure_vision_key: str = ""

    azure_ml_endpoint: str = ""
    azure_ml_key: str = ""

    llm_mode: Literal["ollama", "template"] = "template"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    history_api_base: str = "mock"
    history_api_key: str = ""

    @property
    def vision_is_real(self) -> bool:
        return self.azure_mode == "real" and bool(self.azure_vision_key)

    @property
    def ml_is_real(self) -> bool:
        return self.azure_mode == "real" and bool(self.azure_ml_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
