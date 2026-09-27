"""Tracks today's API spend in a small file, so a restart does not reset the daily cap.
Implements: R8, G5
"""
import json
import threading
from datetime import datetime, timezone

from app import config

_FILE = config.DATA_DIR / "spend.json"
_lock = threading.Lock()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _read() -> dict:
    try:
        return json.loads(_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def cost_of(usage) -> float:
    return (
        usage.input_tokens * config.PRICE_INPUT
        + (usage.cache_creation_input_tokens or 0) * config.PRICE_CACHE_WRITE
        + (usage.cache_read_input_tokens or 0) * config.PRICE_CACHE_READ
        + usage.output_tokens * config.PRICE_OUTPUT
    ) / 1_000_000


def spent_today() -> float:
    with _lock:
        return _read().get(_today(), 0.0)


def add(usd: float) -> float:
    with _lock:
        data = _read()
        today = _today()
        data = {today: data.get(today, 0.0) + usd}
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(json.dumps(data))
        return data[today]


def over_limit() -> bool:
    return spent_today() >= config.DAILY_SPEND_LIMIT_USD
