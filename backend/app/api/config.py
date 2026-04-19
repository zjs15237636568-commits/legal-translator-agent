from __future__ import annotations

from fastapi import APIRouter

from app.core.config import AppConfig, ProviderConfig, load_config, save_config, reload_config
from app.models.schemas import ConfigDTO, ProviderDTO

router = APIRouter(prefix="/api/config", tags=["config"])


def _mask(cfg: AppConfig) -> ConfigDTO:
    """对外脱敏：不返回完整 api_key。"""
    out = {}
    for name, p in cfg.providers.items():
        key = p.get("api_key", "")
        masked = (key[:4] + "***" + key[-2:]) if len(key) >= 8 else ("***" if key else "")
        out[name] = ProviderDTO(api_key=masked, base_url=p.get("base_url", ""), model=p.get("model", ""))
    return ConfigDTO(active_provider=cfg.active_provider, providers=out)


@router.get("", response_model=ConfigDTO)
async def get_config():
    return _mask(load_config())


@router.put("", response_model=ConfigDTO)
async def update_config(body: ConfigDTO):
    cfg = load_config()
    cfg.active_provider = body.active_provider
    for name, p in body.providers.items():
        existing = cfg.providers.get(name, {})
        new_key = p.api_key
        # 如果传入的是掩码形式（包含 ***），保留旧 key
        if "***" in new_key:
            new_key = existing.get("api_key", "")
        cfg.providers[name] = {
            "api_key": new_key,
            "base_url": p.base_url or existing.get("base_url", ""),
            "model": p.model or existing.get("model", ""),
        }
    save_config(cfg)
    reload_config()
    return _mask(cfg)
