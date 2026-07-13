from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_mode: Literal["mock", "real"] = "mock"

    vision_provider: Literal["image_analysis", "custom_vision", "local_http"] = "image_analysis"
    azure_vision_endpoint: str = ""
    azure_vision_key: str = ""
    custom_vision_endpoint: str = ""
    custom_vision_key: str = ""
    custom_vision_project_id: str = ""
    custom_vision_iteration: str = ""

    azure_ml_endpoint: str = ""
    azure_ml_key: str = ""
    azure_ml_input_name: str = "input1"
    azure_ml_output_name: str = "output1"

    llm_mode: Literal["template", "ollama", "gemini", "mistral"] = "template"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"

    @property
    def vision_is_local_http(self) -> bool:
        return self.vision_provider == "local_http" and bool(self.azure_vision_endpoint)

    @property
    def vision_is_real(self) -> bool:
        if self.azure_mode != "real":
            return False
        if self.vision_provider == "custom_vision":
            return bool(self.custom_vision_key)
        return bool(self.azure_vision_key)

    @property
    def ml_is_real(self) -> bool:
        return self.azure_mode == "real" and bool(self.azure_ml_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
