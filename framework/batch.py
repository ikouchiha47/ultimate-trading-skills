"""Resumable, rate-limit-aware batch runner with a tracker JSON.

For multi-item gathering (screener scrapes, filing downloads, per-name backtests) where hitting
a host too fast gets you throttled or banned. Processes items one at a time with a polite delay +
jitter, retries failures with backoff, and persists a tracker after EVERY item so a crash or a
rate-limit stall can resume exactly where it left off (already-done items are skipped).

Generic + thin: you pass the items and a `work_fn(item) -> json-able result`; this owns the
pacing, retry and bookkeeping. The report orchestrator drives it (see research-report SKILL.md).

Tracker JSON schema:
    {
      "created": iso, "updated": iso, "delay": float,
      "items": { "<key>": {"status": "pending|done|failed",
                            "attempts": int, "started": iso, "finished": iso,
                            "output": <result or path>, "error": str|null} }
    }
"""
from __future__ import annotations

import json
import random
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BatchTracker:
    """Load/save the tracker JSON; the single source of progress (crash-safe, resumable)."""

    def __init__(self, path: str | Path, delay: float = 2.0):
        self.path = Path(path)
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            self.data = {"created": _now(), "updated": _now(), "delay": delay, "items": {}}

    def _save(self) -> None:
        self.data["updated"] = _now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, default=str))
        tmp.replace(self.path)                       # atomic — never leave a half-written tracker

    def status(self, key: str) -> str:
        return self.data["items"].get(key, {}).get("status", "pending")

    def mark(self, key: str, status: str, **fields: Any) -> None:
        rec = self.data["items"].setdefault(key, {"status": "pending", "attempts": 0})
        rec["status"] = status
        rec.update(fields)
        self._save()

    def pending(self, keys: Iterable[str], retry_failed: bool = True) -> list[str]:
        todo = []
        for k in keys:
            s = self.status(k)
            if s == "done":
                continue
            if s == "failed" and not retry_failed:
                continue
            todo.append(k)
        return todo

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for rec in self.data["items"].values():
            out[rec["status"]] = out.get(rec["status"], 0) + 1
        return out


def run_batch(items: list[str], work_fn: Callable[[str], Any], tracker_path: str | Path,
              *, delay: float = 2.0, jitter: float = 1.0, max_retries: int = 2,
              backoff: float = 5.0, retry_failed: bool = True,
              key_fn: Callable[[str], str] | None = None) -> BatchTracker:
    """Run `work_fn` over `items`, paced + retried, persisting to `tracker_path`. Resumable.

    - `delay` + random `jitter` seconds between items (be a polite client).
    - `max_retries` extra attempts per item, sleeping `backoff * attempt` between tries.
    - Already-`done` items are skipped; `failed` ones retried unless `retry_failed=False`.
    - `work_fn` must return a JSON-able value (the result, or a path to where it was written).
    Re-run the SAME command after a stall/rate-limit and it picks up the remaining items.
    """
    tr = BatchTracker(tracker_path, delay=delay)
    keyer = key_fn or (lambda x: str(x))
    todo = tr.pending([keyer(i) for i in items], retry_failed=retry_failed)
    todo_set = set(todo)

    first = True
    for item in items:
        key = keyer(item)
        if key not in todo_set:
            continue
        if not first:
            time.sleep(delay + random.uniform(0, jitter))   # pace before each (not the first)
        first = False

        attempts = tr.data["items"].get(key, {}).get("attempts", 0)
        for attempt in range(attempts, attempts + max_retries + 1):
            tr.mark(key, "pending", attempts=attempt + 1, started=_now(), error=None)
            try:
                result = work_fn(item)
                tr.mark(key, "done", finished=_now(), output=result, error=None)
                break
            except Exception as e:  # noqa: BLE001
                msg = f"{type(e).__name__}: {e}"
                if attempt < attempts + max_retries:
                    time.sleep(backoff * (attempt - attempts + 1))   # linear backoff
                    continue
                tr.mark(key, "failed", finished=_now(), error=msg)
    return tr
