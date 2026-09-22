"""One-time Google sign-in for the booking calendar.

Run: .venv/bin/python scripts/google_signin.py
A browser opens. Sign in as the calendar owner and allow access.
The result is saved to secrets/google-token.json (never committed to git).
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",    # create the call events
    "https://www.googleapis.com/auth/calendar.freebusy",  # see which times are free
    "https://www.googleapis.com/auth/gmail.send",         # send founder alert emails
]
CLIENT_FILE = ROOT / os.getenv("GOOGLE_CLIENT_SECRET_FILE", "secrets/client_secret.json")
TOKEN_FILE = ROOT / os.getenv("GOOGLE_TOKEN_FILE", "secrets/google-token.json")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

if not CLIENT_FILE.exists():
    # Accept the file under its downloaded name (Finder can hide or double the .json ending).
    found = sorted(CLIENT_FILE.parent.glob("client_secret*.json"))
    CLIENT_FILE = found[0] if found else CLIENT_FILE
if not CLIENT_FILE.exists():
    sys.exit(f"Missing {CLIENT_FILE.relative_to(ROOT)}. Download the JSON from Google Cloud first (step 5).")

flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent",
                              success_message="Done. You can close this tab and go back to Claude Code.")
TOKEN_FILE.write_text(creds.to_json())
TOKEN_FILE.chmod(0o600)

now = datetime.now(timezone.utc)
calendar = build("calendar", "v3", credentials=creds, cache_discovery=False)
busy = calendar.freebusy().query(body={
    "timeMin": now.isoformat(), "timeMax": (now + timedelta(days=7)).isoformat(),
    "items": [{"id": CALENDAR_ID}],
}).execute()["calendars"][CALENDAR_ID]

if busy.get("errors"):
    sys.exit(f"Signed in, but could not read calendar {CALENDAR_ID}: {busy['errors']}")
print(f"Signed in. Calendar {CALENDAR_ID} is connected.")
print(f"Busy periods in the next 7 days: {len(busy['busy'])}")
print(f"Saved sign-in to {TOKEN_FILE.relative_to(ROOT)} (not saved in git).")
if not creds.refresh_token:
    print("WARNING: Google did not give a long-lasting sign-in. Tell Claude.")
