"""
Configuration module -- loads .env and validates API keys.
Provides a singleton Settings object for the entire application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Settings:
    """Centralized configuration with graceful handling of missing keys."""

    # ── LLM Keys ──────────────────────────────────────────────
    GOOGLE_AI_API_KEY: str | None = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    CEREBRAS_API_KEY: str | None = os.getenv("CEREBRAS_API_KEY")
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")

    # ── External API Keys (Free APIs) ────────────────────────
    SERPER_API_KEY: str | None = os.getenv("SERPER_API_KEY")
    SERPAPI_KEY: str | None = os.getenv("SERPAPI_KEY")
    GEOAPIFY_API_KEY: str | None = os.getenv("GEOAPIFY_API_KEY")
    MAPTILER_API_KEY: str | None = os.getenv("MAPTILER_API_KEY")
    X_RAPIDAPI_KEY: str | None = os.getenv("X_RAPIDAPI_KEY")
    WEATHERAPI_API_KEY: str | None = os.getenv("WEATHERAPI_API_KEY")
    OPENTRIPMAP_API_KEY: str | None = os.getenv("OPENTRIPMAP_API_KEY")

    # ── LLM Model Config ─────────────────────────────────────
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    CEREBRAS_MODEL: str = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")

    # ── Currency Config ──────────────────────────────────────
    DEFAULT_CURRENCY: str = "INR"
    CURRENCY_SYMBOL: str = "₹"

    # ── App Config ────────────────────────────────────────────
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── LangSmith Config ─────────────────────────────────────
    LANGSMITH_TRACING: str = os.getenv("LANGSMITH_TRACING", "false")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_API_KEY: str | None = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "default")

    @classmethod
    def get_available_llm_providers(cls) -> list[str]:
        """Return list of providers that have valid API keys configured."""
        providers = []
        if cls.GOOGLE_AI_API_KEY:
            providers.append("gemini")
        if cls.OPENAI_API_KEY:
            providers.append("openai")
        if cls.CEREBRAS_API_KEY:
            providers.append("cerebras")
        return providers

    @classmethod
    def get_missing_api_keys(cls) -> list[str]:
        """Return list of API keys that are not configured."""
        missing = []
        key_map = {
            "GOOGLE_AI_API_KEY": cls.GOOGLE_AI_API_KEY,
            "SERPER_API_KEY": cls.SERPER_API_KEY,
            "SERPAPI_KEY": cls.SERPAPI_KEY,
            "GEOAPIFY_API_KEY": cls.GEOAPIFY_API_KEY,
            "X_RAPIDAPI_KEY": cls.X_RAPIDAPI_KEY,
            "WEATHERAPI_API_KEY": cls.WEATHERAPI_API_KEY,
            "OPENTRIPMAP_API_KEY": cls.OPENTRIPMAP_API_KEY,
        }
        for name, value in key_map.items():
            if not value:
                missing.append(name)
        return missing

    @classmethod
    def has_any_llm(cls) -> bool:
        return len(cls.get_available_llm_providers()) > 0

    @classmethod
    def get_best_llm_provider(cls) -> str:
        """Select the best available LLM provider."""
        available = cls.get_available_llm_providers()
        if cls.DEFAULT_LLM_PROVIDER in available:
            return cls.DEFAULT_LLM_PROVIDER
        if available:
            return available[0]
        return "gemini"  # Fallback default


settings = Settings()
