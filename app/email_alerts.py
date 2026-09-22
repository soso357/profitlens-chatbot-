"""Sends short plain emails from the booking Gmail account, using the same Google sign-in as the calendar."""
import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app import config


def send(to: list[str], subject: str, body: str) -> bool:
    if not to or not config.GOOGLE_TOKEN_FILE.exists():
        return False
    msg = EmailMessage()
    msg["From"] = f"ProfitLens Chat <{config.GOOGLE_CALENDAR_ID}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        creds = Credentials.from_authorized_user_file(str(config.GOOGLE_TOKEN_FILE))
        gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception:
        return False


def alert_founders(subject: str, body: str) -> bool:
    return send(config.FOUNDER_NOTIFY_EMAILS, subject, body)
