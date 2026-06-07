"""Single config seam — all host/secret/endpoint settings come through here via dotenv.

ENFORCED CONVENTION: code must NOT hardcode endpoints, API keys, model ids, or host paths.
Read them here. `load_dotenv()` runs once on import (searching upward for a `.env`), then
`env()` / `env_bool()` / `env_int()` wrap os.getenv with optional required-enforcement.

See `.env.example` for every recognized variable. Copy it to `.env` and edit (the `.env` file
is gitignored — secrets never get committed). Setup is documented in CLAUDE.md.
"""

from __future__ import annotations

import os
from pathlib import Path

# Candidate locations to search for a .env, in priority order: repo root (this file is
# framework/config.py, so parents[1] = repo root), cwd, then $HOME. Extend as needed.
_ENV_SEARCH_PATHS = (
    Path(__file__).resolve().parents[1] / ".env",
    Path.cwd() / ".env",
    Path.home() / ".env",
)

_ENV_LOADED: Path | None = None


def ensure_env(required: bool = False) -> Path | None:
    """Locate and load the .env, idempotently. ENFORCED entrypoint (call before reading config).

    Loops the candidate paths (repo root -> cwd -> $HOME) and loads the first that exists. Safe
    to call repeatedly (loads once). With required=True, raises if no .env is found anywhere.
    """
    global _ENV_LOADED
    if _ENV_LOADED is not None:
        return _ENV_LOADED
    try:
        from dotenv import load_dotenv
    except ImportError:  # python-dotenv is in base deps, but stay importable without it
        if required:
            raise ConfigError("python-dotenv not installed (pip install -e .)") from None
        return None
    for candidate in _ENV_SEARCH_PATHS:
        if candidate.exists():
            load_dotenv(candidate)
            _ENV_LOADED = candidate
            return candidate
    if required:
        searched = ", ".join(str(p) for p in _ENV_SEARCH_PATHS)
        raise ConfigError(f"no .env found (searched: {searched}); copy .env.example -> .env")
    return None


class ConfigError(RuntimeError):
    """A required configuration variable is missing, or no .env could be found."""


# Load on import so plain `env(...)` calls work, but ensure_env() may be called explicitly
# (e.g. ensure_env(required=True)) at a program's entrypoint to enforce presence.
ensure_env()


def env(key: str, default: str | None = None, *, required: bool = False) -> str | None:
    val = os.getenv(key, default)
    if required and (val is None or val == ""):
        raise ConfigError(f"required env var {key!r} is not set (see .env.example / CLAUDE.md)")
    return val


def env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ConfigError(f"env var {key!r} must be an integer, got {raw!r}") from e


# --- Convenience accessors for the common settings (single source of truth) ---------------

def ollama_endpoint() -> str:
    return env("OLLAMA_ENDPOINT", "http://localhost:11434")


def vision_model() -> str:
    return env("VISION_MODEL", "qwen2.5vl:3b")
