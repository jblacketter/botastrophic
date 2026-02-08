"""LLM client abstraction layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from api.app.config import get_settings


@dataclass
class LLMResponse:
    """Response from LLM call."""
    content: str
    input_tokens: int
    output_tokens: int
    model: str


class LLMClient(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def think(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.8,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send prompt to LLM and get response."""
        pass


def get_llm_client() -> LLMClient:
    """Factory function to get the configured LLM client."""
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        from api.app.llm.anthropic import AnthropicAdapter
        return AnthropicAdapter(api_key=settings.anthropic_api_key)
    elif provider == "mock":
        from api.app.llm.mock import MockAdapter
        return MockAdapter()
    elif provider == "ollama":
        from api.app.llm.ollama import OllamaAdapter
        return OllamaAdapter(base_url=settings.ollama_base_url)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
