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
