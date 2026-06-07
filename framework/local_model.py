"""Config-gated local-model client (Ollama via langchain) for skill fallbacks.

Governance (mirrors the seam's no-silent-behavior rule):
  - The vision fallback runs ONLY if LOCAL_VISION_ENABLED=true in .env (config-gated).
  - .env (via framework/config.py) is the SINGLE declared place for the endpoint (where data
    goes) and VISION_DATA_POLICY (what may leave the machine). This module enforces both.
  - Not enabled / not installed / unreachable -> raises with a clear reason. Never silent.

Primary use: a local vision model (qwen2.5vl:3b via Ollama) as a fallback for technical-analyst
chart reading — batch/offline, without spending host-model tokens. Default vision is still the
host agent; this path is opt-in per skill.

DESIGN (how to use the vision model well):
  - It is a STRUCTURED-EXTRACTION tool, not a narrator. Ask pointed questions that return a
    single value/label/colour ("What number labels the tallest bar?", "Which bar is the
    lightest green?"). qwen2.5vl:3b is validated for chart number-OCR + colour reading.
  - COMPUTE STAYS WITH THE AGENT (Claude/opencode). The vision model extracts raw perceptions
    (numbers, colours used as a metric dimension); the agent runner does the reasoning,
    aggregation, and scenario logic. Never ask it to compute or judge.

Deps live in the [local] extra (langchain-ollama); Pillow (already present) preps the image.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from framework import config


class LocalModelUnavailable(RuntimeError):
    """Raised when the local model is disabled, misconfigured, or unreachable."""


def vision_config() -> dict:
    """Return the ENABLED vision-model settings from .env, or raise (config-gated)."""
    config.ensure_env()
    if not config.env_bool("LOCAL_VISION_ENABLED", False):
        raise LocalModelUnavailable(
            "local vision is disabled (set LOCAL_VISION_ENABLED=true in .env to allow it)")
    return {
        "endpoint": config.ollama_endpoint(),
        "model": config.vision_model(),
        "data_policy": config.env("VISION_DATA_POLICY", "image-only"),
        "max_image_px": config.env_int("VISION_MAX_IMAGE_PX", 1536),
    }


def _prep_image_b64(image_path: str | Path, max_px: int) -> str:
    """Load, enforce the size policy (downscale), and base64-encode — Pillow."""
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    if max(img.size) > max_px:
        ratio = max_px / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def vision(image_path: str | Path, prompt: str) -> str:
    """Run a chart image + prompt through the configured local vision model.

    Enforces data_policy='image-only': ONLY the image + prompt are sent, nothing else. Returns
    the model's text. Raises LocalModelUnavailable if disabled/uninstalled/unreachable.
    """
    cfg = vision_config()
    if cfg.get("data_policy") != "image-only":
        raise LocalModelUnavailable(
            "VISION_DATA_POLICY must be 'image-only' to send a chart image")
    # langchain ChatOllama — provider-agnostic (swap Ollama↔cloud↔dspy later). Validated with
    # qwen2.5vl (reads SBIN:33,PNB:24,CANBK:30 exactly). The data: URI content format works.
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage
    except ImportError as e:
        raise LocalModelUnavailable(
            f"local vision needs the [local] extra (langchain-ollama): {e}") from None

    b64 = _prep_image_b64(image_path, cfg["max_image_px"])
    llm = ChatOllama(model=cfg["model"], base_url=cfg["endpoint"], temperature=0)
    msg = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": f"data:image/png;base64,{b64}"},
    ])
    try:
        return llm.invoke([msg]).content
    except Exception as e:  # noqa: BLE001 — connection/runtime issues surface clearly
        raise LocalModelUnavailable(
            f"local vision call to {cfg['endpoint']} ({cfg['model']}) failed: {e}") from None


def extract(image_path: str | Path, question: str) -> str:
    """Structured single-value extraction from a chart image (the vision model's intended use).

    `question` MUST be pointed and answerable with one value/label/colour — the agent runner
    then does any computation. Thin wrapper over vision() to make the intent explicit at call
    sites (skills should call this, not ask for prose).
    """
    return vision(image_path, question).strip()
