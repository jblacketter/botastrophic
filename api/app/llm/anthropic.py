"""Anthropic Claude adapter."""

import anthropic

from api.app.llm.client import LLMClient, LLMResponse


class AnthropicAdapter(LLMClient):
    """Adapter for Anthropic Claude API."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def think(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.8,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send prompt to Claude and get response."""
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        return LLMResponse(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=model,
        )
