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
