"""
应用配置与 API Key 加密存储。

- 配置文件：./data/config.enc  (AES-GCM 加密)
- 主密钥：./data/.master.key   (首次运行自动生成)
- 术语库：./data/glossary.json
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.enc"
MASTER_KEY_FILE = DATA_DIR / ".master.key"
GLOSSARY_FILE = DATA_DIR / "glossary.json"
DB_FILE = DATA_DIR / "app.db"


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class ProviderConfig:
    api_key: str = ""
    base_url: str = ""
    model: str = ""


@dataclass
class AppConfig:
    active_provider: str = "deepseek"  # openai / claude / deepseek
    providers: dict = field(default_factory=lambda: {
        "openai":   asdict(ProviderConfig(base_url="https://api.openai.com/v1",      model="gpt-4o")),
        "claude":   asdict(ProviderConfig(base_url="https://api.anthropic.com",      model="claude-sonnet-4-20250514")),
        "deepseek": asdict(ProviderConfig(base_url="https://api.deepseek.com",       model="deepseek-chat")),
    })

    @classmethod
    def default(cls) -> "AppConfig":
        return cls()

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "AppConfig":
        data = json.loads(raw)
        return cls(**data)

    def get_active(self) -> ProviderConfig:
        p = self.providers.get(self.active_provider) or {}
        return ProviderConfig(**p)


# ---------------------------------------------------------------------------
# 加密工具
# ---------------------------------------------------------------------------
def _get_or_create_master_key() -> bytes:
    if MASTER_KEY_FILE.exists():
        return base64.b64decode(MASTER_KEY_FILE.read_text().strip())
    key = AESGCM.generate_key(bit_length=256)
    MASTER_KEY_FILE.write_text(base64.b64encode(key).decode())
    try:
        os.chmod(MASTER_KEY_FILE, 0o600)
    except Exception:
        pass
    return key


def _encrypt(plaintext: str) -> bytes:
    key = _get_or_create_master_key()
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ct


def _decrypt(blob: bytes) -> str:
    key = _get_or_create_master_key()
    aes = AESGCM(key)
    nonce, ct = blob[:12], blob[12:]
    return aes.decrypt(nonce, ct, None).decode("utf-8")


# ---------------------------------------------------------------------------
# 对外 API
# ---------------------------------------------------------------------------
_cache: Optional[AppConfig] = None


def load_config() -> AppConfig:
    global _cache
    if _cache is not None:
        return _cache
    if not CONFIG_FILE.exists():
        _cache = AppConfig.default()
        save_config(_cache)
        return _cache
    try:
        raw = _decrypt(CONFIG_FILE.read_bytes())
        _cache = AppConfig.from_json(raw)
    except Exception:
        # 损坏则重建
        _cache = AppConfig.default()
        save_config(_cache)
    return _cache


def save_config(cfg: AppConfig) -> None:
    global _cache
    CONFIG_FILE.write_bytes(_encrypt(cfg.to_json()))
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass
    _cache = cfg


def reload_config() -> AppConfig:
    global _cache
    _cache = None
    return load_config()
