"""Ollama adapter for local LLM models."""

import logging
import httpx

from api.app.llm.client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)


class OllamaAdapter(LLMClient):
    """Adapter for Ollama local models (Llama 3 8B, Mistral, etc.)."""

    DEFAULT_MODEL = "llama3"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def think(
        self,
        prompt: str,
        model: str = "llama3",
        temperature: float = 0.8,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a response using Ollama."""
        # Override non-Ollama model names (e.g. claude-*) with the default local model
        if model.startswith("claude") or model.startswith("gpt"):
            model = self.DEFAULT_MODEL
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data.get("response", ""),
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
                model=model,
            )
