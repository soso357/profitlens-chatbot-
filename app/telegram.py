"""Sends founder alerts to the Telegram group."""
import json
import ssl
import urllib.parse
import urllib.request

import certifi

from app import config

# Python's built-in certificate list is missing on some Macs, so use certifi's.
_SSL = ssl.create_default_context(cafile=certifi.where())


def send(text: str) -> bool:
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        return False
    data = urllib.parse.urlencode({"chat_id": config.TELEGRAM_CHAT_ID, "text": text}).encode()
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        with urllib.request.urlopen(url, data, timeout=10, context=_SSL) as r:
            return bool(json.load(r).get("ok"))
    except Exception:
        return False


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
