"""Writes every message and guardrail event to logs/conversations.jsonl, one line each."""
import json
import threading
from datetime import datetime, timezone

from app import config

_FILE = config.LOG_DIR / "conversations.jsonl"
_lock = threading.Lock()


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
