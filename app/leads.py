"""Saves every lead to leads.csv on the server (Phase 2, spec section 5).
The "fit" column stays (left empty) so older files still read; fit is no longer asked (B5 retired 2026-09-28).
Implements: B4, B7
"""
import csv
import threading
from datetime import datetime, timezone

from app import config

FILE = config.DATA_DIR / "leads.csv"
COLUMNS = ["time_utc", "session_id", "name", "restaurant", "location", "email", "fit", "outcome", "call_time", "source"]
_lock = threading.Lock()


def save(session_id: str, details: dict, outcome: str, call_time: str = "", source: str = "") -> None:
    row = {
        "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": session_id,
        **{k: details.get(k, "") for k in ("name", "restaurant", "location", "email", "fit")},
        "outcome": outcome,
        "call_time": call_time,
        "source": source,
    }
    with _lock:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        new = not FILE.exists()
        with FILE.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            if new:
                w.writeheader()
            w.writerow(row)
