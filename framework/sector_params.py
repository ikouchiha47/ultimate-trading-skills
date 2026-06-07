"""Per-sector strategy parameters — the earned reversion anchor, read + written.

Single source: data/sector_strategy.toml. The anchor is NOT defaulted — a sector that has
not been calibrated raises NotCalibrated so the orchestrator (SKILL.md) runs the calibration
sweep, judges the result, and writes it back via set_anchor. Code provides primitives; the
agent decides. See skills/edge-pipeline/strategy-harness/SKILL.md.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "data" / "sector_strategy.toml"


class NotCalibrated(LookupError):
    """Raised when a sector has no earned anchor yet — calibrate, don't default."""


def _load(path: Path | None = None) -> dict:
    with open(path or _PATH, "rb") as fh:
        return tomllib.load(fh)


def candidates() -> list[int]:
    """Anchor values the calibrator sweeps for an un-calibrated sector."""
    return [int(x) for x in _load().get("candidates", [25, 50, 100, 200])]


def reversion_anchor(sector: str) -> int:
    """Earned reversion DMA for a sector, or raise NotCalibrated (no silent default)."""
    anchors = _load().get("anchor", {})
    if sector not in anchors:
        raise NotCalibrated(
            f"no earned reversion anchor for {sector!r}; run "
            f"framework.calibrate.calibrate_anchor({sector!r}) and persist with set_anchor()")
    return int(anchors[sector])


def is_calibrated(sector: str) -> bool:
    return sector in _load().get("anchor", {})


def set_anchor(sector: str, ma: int, note: str, path: Path | None = None) -> None:
    """Persist an earned anchor + its provenance note back to the toml (single source)."""
    p = path or _PATH
    data = _load(p)
    data.setdefault("anchor", {})[sector] = int(ma)
    data.setdefault("note", {})[sector] = str(note)
    _dump(data, p)


def _dump(data: dict, path: Path) -> None:
    """Tiny serializer for this file's known schema (avoids a tomli-w dependency)."""
    lines = [
        "# Per-sector strategy parameters — EDIT HERE, not in code.",
        "# Read via framework.sector_params; written back by the calibration step.",
        "# Absent sector = MUST calibrate (no silent default); see the strategy-harness SKILL.md.",
        "",
        "candidates = [" + ", ".join(str(int(x)) for x in data.get("candidates", [25, 50, 100, 200])) + "]",
        "",
        "[anchor]",
    ]
    for sec, ma in data.get("anchor", {}).items():
        lines.append(f'"{sec}" = {int(ma)}')
    lines += ["", "[note]"]
    for sec, note in data.get("note", {}).items():
        esc = str(note).replace('"', '\\"')
        lines.append(f'"{sec}" = "{esc}"')
    path.write_text("\n".join(lines) + "\n")
