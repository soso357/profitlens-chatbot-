"""Settings, read from environment variables (the .env file locally, Render settings later)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


CONTENT_DIR = ROOT / "content"
LOG_DIR = Path(os.getenv("LOG_DIR", ROOT / "logs"))
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))

MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")
# Haiku 4.5 prices in US dollars per million tokens.
PRICE_INPUT = _float("PRICE_INPUT_PER_M", 1.00)
PRICE_OUTPUT = _float("PRICE_OUTPUT_PER_M", 5.00)
PRICE_CACHE_WRITE = _float("PRICE_CACHE_WRITE_PER_M", 1.25)
PRICE_CACHE_READ = _float("PRICE_CACHE_READ_PER_M", 0.10)

# Cost and abuse protection (rule 8).
MAX_REPLY_TOKENS = _int("MAX_REPLY_TOKENS", 400)
MAX_MESSAGE_CHARS = _int("MAX_MESSAGE_CHARS", 1000)
SESSION_MESSAGES_PER_HOUR = _int("SESSION_MESSAGES_PER_HOUR", 20)
MAX_VISITOR_MESSAGES_PER_SESSION = _int("MAX_VISITOR_MESSAGES_PER_SESSION", 30)
IP_RATE_LIMIT = os.getenv("IP_RATE_LIMIT", "60/hour")
DAILY_SPEND_LIMIT_USD = _float("DAILY_SPEND_LIMIT_USD", 5.00)

# Booking (Phase 3). Founders' hours are in their own time zone; an end before the start runs past midnight.
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
GOOGLE_TOKEN_FILE = ROOT / os.getenv("GOOGLE_TOKEN_FILE", "secrets/google-token.json")
BOOKING_TIMEZONE = os.getenv("BOOKING_TIMEZONE", "Asia/Tbilisi")
BOOKING_DAYS = os.getenv("BOOKING_DAYS", "mon,tue,wed,thu,fri,sat,sun").split(",")
BOOKING_START = os.getenv("BOOKING_START", "19:00")
BOOKING_END = os.getenv("BOOKING_END", "03:00")
CALL_MINUTES = _int("CALL_MINUTES", 20)
SLOT_STEP_MINUTES = _int("SLOT_STEP_MINUTES", 30)
BOOKING_MIN_NOTICE_HOURS = _int("BOOKING_MIN_NOTICE_HOURS", 12)
BOOKING_HORIZON_DAYS = _int("BOOKING_HORIZON_DAYS", 14)

# Founder alerts.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
FOUNDER_NOTIFY_EMAILS = [e.strip() for e in os.getenv("FOUNDER_NOTIFY_EMAIL", "").split(",") if e.strip()]

# Local test pages (never switch on in production).
TEST_PAGES = os.getenv("TEST_PAGES", "") == "1"
