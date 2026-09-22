from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import settings


@dataclass
class LLMClient:
    """Small OpenAI-compatible client for the server-side vLLM endpoint."""

    base_url: str = settings.llm_base_url
    api_key: str = settings.llm_api_key
    model: str = settings.llm_model
    timeout: float = 90.0

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 512,
        model: str | None = None,
    ) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - environment guidance
            raise RuntimeError("Install the 'openai' package to use the LLM mode") from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
        response = client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        return response.choices[0].message.content or ""


def chat(messages: list[dict[str, str]], **kwargs: Any) -> str:
    return LLMClient().chat(messages, **kwargs)

