"""
OpenAI 兼容协议 Provider（同时服务 OpenAI 和 DeepSeek）。

- OpenAI  : base_url = https://api.openai.com/v1
- DeepSeek: base_url = https://api.deepseek.com   (兼容 OpenAI Chat Completions)
"""
from __future__ import annotations

from typing import AsyncIterator

from openai import AsyncOpenAI


class OpenAILikeProvider:
    def __init__(self, *, name: str, api_key: str, base_url: str, model: str):
        self.name = name
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def stream_chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> str:
        kwargs: dict = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response_format is not None:
            kwargs["response_format"] = response_format
        resp = await self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
