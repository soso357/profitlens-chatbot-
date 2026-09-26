"""Sends short plain emails from the booking Gmail account, using the same Google sign-in as the calendar."""
import base64
from email.message import EmailMessage

import google_auth_httplib2
import httplib2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app import alert_health, config


def _creds() -> Credentials:
    creds = Credentials.from_authorized_user_file(str(config.GOOGLE_TOKEN_FILE))
    if not creds.valid:
        creds.refresh(google_auth_httplib2.Request(httplib2.Http(timeout=10)))
    return creds


def _deliver(raw: str) -> None:
    """Hands one message to Gmail. Tests replace this."""
    gmail = build("gmail", "v1", credentials=_creds(), cache_discovery=False)
    gmail.users().messages().send(userId="me", body={"raw": raw}).execute()


def _failed(e: Exception) -> tuple[str, str]:
    why = f"{type(e).__name__}: {str(e)[:200]}"
    if "invalid_grant" in why or "expired" in why.lower() or "revoked" in why.lower():
        return why, ("the Google sign-in has expired or was revoked. Run scripts/google_signin.py on the Mac, "
                     "then upload the new secrets/google-token.json to Render as the secret file google-token.json.")
    return why, ""


def _ready(to: list[str]) -> bool:
    if not to:
        alert_health.record("email", False, "FOUNDER_NOTIFY_EMAIL is not set", "on Render, add FOUNDER_NOTIFY_EMAIL.")
        return False
    if not config.GOOGLE_TOKEN_FILE.exists():
        alert_health.record("email", False, "the Google sign-in file is missing",
                            "upload secrets/google-token.json to Render as the secret file google-token.json.")
        return False
    return True


def send(to: list[str], subject: str, body: str) -> bool:
    if not _ready(to):
        return False
    msg = EmailMessage()
    msg["From"] = f"ProfitLens Chat <{config.GOOGLE_CALENDAR_ID}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        _deliver(base64.urlsafe_b64encode(msg.as_bytes()).decode())
    except Exception as e:
        alert_health.record("email", False, *_failed(e))
        return False
    alert_health.record("email", True)
    return True


def check() -> bool:
    """Startup check (ADR 0021): settings present and the Google sign-in still works. Sends nothing."""
    if not _ready(config.FOUNDER_NOTIFY_EMAILS):
        return False
    try:
        _creds()
    except Exception as e:
        alert_health.record("email", False, *_failed(e))
        return False
    alert_health.record("email", True)
    return True


def alert_founders(subject: str, body: str) -> bool:
    return send(config.FOUNDER_NOTIFY_EMAILS, subject, body)
