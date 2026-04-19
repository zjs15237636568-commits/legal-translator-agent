"""
LLM Router：根据当前配置返回对应 Provider 实例。
"""
from __future__ import annotations

from app.core.config import load_config

from .base import LLMProvider
from .claude import ClaudeProvider
from .openai_like import OpenAILikeProvider


class LLMConfigError(RuntimeError):
    pass


def get_provider() -> LLMProvider:
    cfg = load_config()
    name = cfg.active_provider
    provider_cfg = cfg.get_active()

    if not provider_cfg.api_key:
        raise LLMConfigError(
            f"Provider '{name}' API key not configured. Please set it in Settings."
        )

    if name in ("openai", "deepseek"):
        return OpenAILikeProvider(
            name=name,
            api_key=provider_cfg.api_key,
            base_url=provider_cfg.base_url,
            model=provider_cfg.model,
        )
    if name == "claude":
        return ClaudeProvider(
            api_key=provider_cfg.api_key,
            base_url=provider_cfg.base_url,
            model=provider_cfg.model,
        )
    raise LLMConfigError(f"Unknown provider: {name}")


__all__ = ["get_provider", "LLMProvider", "LLMConfigError"]
