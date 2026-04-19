"""
Anthropic Claude Provider。
"""
from __future__ import annotations

from typing import AsyncIterator

from anthropic import AsyncAnthropic


def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    """Anthropic 要求 system 单独传，其他消息中的 system 合并。"""
    system_parts: list[str] = []
    rest: list[dict] = []
    for m in messages:
        if m.get("role") == "system":
            system_parts.append(m.get("content", ""))
        else:
            rest.append({"role": m["role"], "content": m["content"]})
    return "\n\n".join(p for p in system_parts if p), rest


class ClaudeProvider:
    def __init__(self, *, api_key: str, base_url: str, model: str):
        self.name = "claude"
        self.model = model
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncAnthropic(**kwargs)

    async def stream_chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        system, rest = _split_system(messages)
        async with self._client.messages.stream(
            model=self.model,
            system=system or None,
            messages=rest,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        ) as stream:
            async for text in stream.text_stream:
                if text:
                    yield text

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        response_format: dict | None = None,  # Claude 不直接支持，忽略
    ) -> str:
        system, rest = _split_system(messages)
        resp = await self._client.messages.create(
            model=self.model,
            system=system or None,
            messages=rest,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
        # resp.content 是一个 block 列表
        parts = []
        for b in resp.content:
            if getattr(b, "type", None) == "text":
                parts.append(b.text)
        return "".join(parts)
