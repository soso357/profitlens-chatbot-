"""Sends founder alerts to the Telegram group. Failures are reported, not swallowed (ADR 0021)."""
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request

import certifi

from app import alert_health, config

# Python's built-in certificate list is missing on some Macs, so use certifi's.
_SSL = ssl.create_default_context(cafile=certifi.where())


def _call(method: str, params: dict) -> tuple[bool, dict]:
    """One Telegram Bot API call. Returns (ok, Telegram's answer). Tests replace this."""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}"
    try:
        with urllib.request.urlopen(url, urllib.parse.urlencode(params).encode(), timeout=10, context=_SSL) as r:
            answer = json.load(r)
    except urllib.error.HTTPError as e:  # Telegram explains 4xx errors in the body
        try:
            answer = json.load(e)
        except Exception:
            answer = {"description": f"HTTP {e.code}"}
    except Exception as e:
        answer = {"description": f"could not reach Telegram ({type(e).__name__})"}
    return bool(answer.get("ok")), answer


def _explain(answer: dict) -> tuple[str, str]:
    """(reason, what to do) from a failed Telegram answer. Never contains the token."""
    why = str(answer.get("description") or "unknown error")
    new_id = (answer.get("parameters") or {}).get("migrate_to_chat_id")
    if new_id:
        return (f"{why}. New chat ID: {new_id}",
                f"on Render, set TELEGRAM_CHAT_ID to {new_id} and save (the service restarts by itself).")
    low = why.lower()
    if answer.get("error_code") == 401 or "unauthorized" in low:
        hint = ("the bot token is wrong or was revoked. Get the token from BotFather for @profitlbot and update "
                "TELEGRAM_BOT_TOKEN on Render.")
    elif "chat not found" in low or "kicked" in low or "not a member" in low:
        hint = "check that @profitlbot is still in the ProfitLens leads group and that TELEGRAM_CHAT_ID on Render is right."
    elif "could not reach" in low:
        hint = "usually a short network problem. If it keeps failing, check Telegram's status."
    else:
        hint = ""
    return why.replace(config.TELEGRAM_BOT_TOKEN or "\0", "[token]"), hint


def _result(ok: bool, answer: dict) -> bool:
    if ok:
        alert_health.record("telegram", True)
    else:
        alert_health.record("telegram", False, *_explain(answer))
    return ok


def _configured() -> bool:
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        return True
    alert_health.record("telegram", False, "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set",
                        "on Render, add both settings (Environment tab).")
    return False


def send(text: str) -> bool:
    if not _configured():
        return False
    return _result(*_call("sendMessage", {"chat_id": config.TELEGRAM_CHAT_ID, "text": text}))


def check() -> bool:
    """Startup check (ADR 0021): does the bot see the chat? Posts nothing."""
    if not _configured():
        return False
    return _result(*_call("getChat", {"chat_id": config.TELEGRAM_CHAT_ID}))


def send_long(text: str, limit: int = 3900) -> bool:
    """Telegram allows 4096 characters per message; split long texts on line breaks."""
    chunks, current = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) > limit:
            chunks.append(current)
            current = ""
        current += line
    if current:
        chunks.append(current)
    total = len(chunks)
    ok = True
    for i, chunk in enumerate(chunks, 1):
        ok = send(chunk if total == 1 else f"({i}/{total})\n{chunk}") and ok
    return ok
