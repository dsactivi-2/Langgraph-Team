from __future__ import annotations

from openai import OpenAI

from .settings import get_settings


class LLMUnavailable(RuntimeError):
    pass


class OpenAICompatibleLLM:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.openai_api_key)

    def complete(self, prompt: str, system: str | None = None) -> str:
        if not self.settings.openai_api_key:
            raise LLMUnavailable("OPENAI_API_KEY is not configured")
        client = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.llm_base_url,
        )
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=self.settings.llm_model,
            messages=messages,
        )
        return response.choices[0].message.content or ""
