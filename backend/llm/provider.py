"""
Multi-provider LLM abstraction layer.
Dynamically selects between OpenAI, Google Gemini, and Cerebras.
"""

from __future__ import annotations
import logging
from langchain_core.language_models import BaseChatModel
from backend.config import settings

logger = logging.getLogger(__name__)

# ── Provider Registry ─────────────────────────────────────────

_llm_cache: dict[str, BaseChatModel] = {}


class LLMProviderFactory:
    """Factory that creates and caches LLM instances per provider."""

    @staticmethod
    def create_gemini(temperature: float = 0.3) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_AI_API_KEY,
            temperature=temperature,
            convert_system_message_to_human=True,
        )

    @staticmethod
    def create_openai(temperature: float = 0.3) -> BaseChatModel:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
        )

    @staticmethod
    def create_cerebras(temperature: float = 0.3) -> BaseChatModel:
        from langchain_cerebras import ChatCerebras
        return ChatCerebras(
            model=settings.CEREBRAS_MODEL,
            api_key=settings.CEREBRAS_API_KEY,
            temperature=temperature,
        )

    @classmethod
    def get(cls, provider: str | None = None, temperature: float = 0.3) -> BaseChatModel:
        """Get an LLM instance for the specified (or best available) provider."""
        provider = provider or settings.get_best_llm_provider()
        cache_key = f"{provider}_{temperature}"

        if cache_key in _llm_cache:
            return _llm_cache[cache_key]

        creators = {
            "gemini": cls.create_gemini,
            "openai": cls.create_openai,
            "cerebras": cls.create_cerebras,
        }

        if provider not in creators:
            raise ValueError(f"Unknown LLM provider: {provider}. Supported: {list(creators.keys())}")

        logger.info(f"Creating LLM instance: provider={provider}, temperature={temperature}")
        llm = creators[provider](temperature=temperature)
        _llm_cache[cache_key] = llm
        return llm


def get_llm(provider: str | None = None, temperature: float = 0.3) -> BaseChatModel:
    """Convenience function to get an LLM instance."""
    return LLMProviderFactory.get(provider, temperature)
