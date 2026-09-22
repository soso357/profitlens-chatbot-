"""Sends short plain emails through Zoho Mail (EU servers)."""
import smtplib
import ssl
from email.message import EmailMessage

import certifi

from app import config

_SSL = ssl.create_default_context(cafile=certifi.where())


def send(to: list[str], subject: str, body: str) -> bool:
    if not (config.ZOHO_SMTP_USER and config.ZOHO_SMTP_PASSWORD and to):
        return False
    msg = EmailMessage()
    msg["From"] = f"ProfitLens Chat <{config.ZOHO_SMTP_USER}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP_SSL(config.ZOHO_SMTP_HOST, 465, context=_SSL, timeout=15) as smtp:
            smtp.login(config.ZOHO_SMTP_USER, config.ZOHO_SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception:
        return False


def alert_founders(subject: str, body: str) -> bool:
    return send(config.FOUNDER_NOTIFY_EMAILS, subject, body)
