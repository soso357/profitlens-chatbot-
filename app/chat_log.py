"""Writes every message and guardrail event to logs/conversations.jsonl, one line each,
and deletes lines older than 30 days (ADR 0027).
Implements: R9
"""
import json
import threading
from datetime import datetime, timedelta, timezone

from app import config

_FILE = config.LOG_DIR / "conversations.jsonl"
_lock = threading.Lock()
KEEP_DAYS = 30


def log(session_id: str, event: str, **fields) -> None:
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": session_id,
        "event": event,
        **fields,
    }
    with _lock:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _is_recent(line: str, cutoff: datetime) -> bool:
    try:
        return datetime.fromisoformat(json.loads(line)["time"]) >= cutoff
    except (ValueError, KeyError, TypeError):
        return False  # unreadable lines are dropped


def delete_old(days: int = KEEP_DAYS) -> int:
    """R9: keep only log lines from the last `days` days. Returns how many lines were deleted."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with _lock:  # no message can be written while the file is rewritten
        if not _FILE.exists():
            return 0
        lines = _FILE.read_text(encoding="utf-8").splitlines(keepends=True)
        keep = [line for line in lines if _is_recent(line, cutoff)]
        if len(keep) < len(lines):
            tmp = _FILE.with_suffix(".tmp")
            tmp.write_text("".join(keep), encoding="utf-8")
            tmp.replace(_FILE)
        return len(lines) - len(keep)
