"""Runtime configuration, read once from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    """Read a positive integer from the environment, falling back safely."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_timeout_ms: int = 45_000
    rate_limit_per_minute: int = 10
    cache_size: int = 128
    max_request_bytes: int = 16 * 1024
    timezone: str = "Asia/Kolkata"
    trust_proxy: bool = False


def load_settings() -> Settings:
    """Build :class:`Settings` from the environment (and an optional .env file)."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:  # pragma: no cover - python-dotenv is optional at runtime
        pass

    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash",
        gemini_timeout_ms=_int_env("GEMINI_TIMEOUT_MS", 45_000, 1_000),
        rate_limit_per_minute=_int_env("RATE_LIMIT_PER_MINUTE", 10),
        cache_size=_int_env("CACHE_SIZE", 128),
        max_request_bytes=_int_env("MAX_REQUEST_BYTES", 16 * 1024, 1_024),
        timezone=os.getenv("APP_TIMEZONE", "Asia/Kolkata").strip(),
        trust_proxy=os.getenv("TRUST_PROXY", "0") == "1",
    )
