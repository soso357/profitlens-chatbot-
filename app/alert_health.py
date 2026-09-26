"""Alert channels fail loudly (proposal 0013, ADR 0021).

Remembers the last result of each founder alert channel. When one fails, the reason and the
fix go to the founders through the other channel, at most once an hour per channel.
In memory only: no visitor data, nothing secret, reset when the service restarts.
"""
import threading
import time

from app import config

WARN_EVERY_SECONDS = 3600
WARN_IN_BACKGROUND = True  # tests set False to see the warning at once

_lock = threading.Lock()
_state = {"telegram": {"ok": None, "reason": "", "at": 0.0}, "email": {"ok": None, "reason": "", "at": 0.0}}
_last_warned = {"telegram": 0.0, "email": 0.0}


def record(channel: str, ok: bool, reason: str = "", hint: str = "") -> None:
    now = time.time()
    with _lock:
        _state[channel] = {"ok": ok, "reason": "" if ok else reason, "at": now}
        warn = not ok and now - _last_warned[channel] >= WARN_EVERY_SECONDS
        if warn:
            _last_warned[channel] = now
        elif ok:
            _last_warned[channel] = 0.0  # recovered: a new failure is reported at once, not an hour later
    if warn:
        if WARN_IN_BACKGROUND:
            threading.Thread(target=_warn, args=(channel, reason, hint), daemon=True).start()
        else:
            _warn(channel, reason, hint)


def status() -> dict:
    """For /health: 'ok', 'failing' or 'unknown' per channel. No reasons: the page is public."""
    with _lock:
        return {c: "unknown" if s["ok"] is None else "ok" if s["ok"] else "failing" for c, s in _state.items()}


def reason(channel: str) -> str:
    with _lock:
        return _state[channel]["reason"]


def _warn(channel: str, why: str, hint: str) -> None:
    from app import email_alerts, telegram  # here, not at the top: both import this module
    tag = " (LOCAL TEST)" if config.TEST_PAGES else ""
    if channel == "telegram":
        email_alerts.alert_founders(
            f"ProfitLens chat: Telegram alerts are failing{tag}",
            f"The chat service could not post to the founders' Telegram group.\n\nReason: {why}\n"
            f"What to do: {hint or 'check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID on Render.'}\n\n"
            "Leads and bookings still arrive by email. This warning repeats at most once an hour while the "
            "problem lasts.")
    else:
        telegram.send(
            f"ProfitLens chat: founder emails are failing{tag}\n\nReason: {why}\n"
            f"What to do: {hint or 'check FOUNDER_NOTIFY_EMAIL and the Google sign-in file on Render.'}\n\n"
            "Leads and bookings still arrive here in Telegram. This warning repeats at most once an hour "
            "while the problem lasts.")
