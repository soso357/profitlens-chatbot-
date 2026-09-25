"""Conversations that survive a restart (ADR 0018).

Sessions live in memory, and Render restarts the service on every deploy and, on the
free plan, after 15 quiet minutes. So after every reply the server hands the browser a
sealed copy of the conversation (compressed JSON plus an HMAC signature, a tamper proof
seal made with a server secret). The widget sends it back with each request; if the server
no longer has the session in memory, it rebuilds it from the copy. A visitor cannot change
the copy (for example add a fake "you promised a discount" reply): the seal would break
and the copy is ignored.
"""
import base64
import hashlib
import hmac
import json
import os
import time
import zlib
from datetime import datetime

from app import chat_booking

MAX_TOKEN_CHARS = 120_000
MAX_AGE_SECONDS = 24 * 3600


def _secret() -> bytes:
    """SESSION_SECRET if set; otherwise derived from the API key, which is also stable across restarts."""
    s = os.getenv("SESSION_SECRET") or ("profitlens-session:" + os.getenv("ANTHROPIC_API_KEY", "local-dev"))
    return hashlib.sha256(s.encode()).digest()


def _sign(data: bytes) -> str:
    return base64.urlsafe_b64encode(hmac.new(_secret(), data, hashlib.sha256).digest()[:24]).decode().rstrip("=")


def dump(session_id: str, session) -> str:
    b = session.booking
    state = {
        "sid": session_id,
        "issued": int(time.time()),
        "created": int(session.created),
        "messages": session.messages,
        "visitor_messages": session.visitor_messages,
        "sent_to_telegram": session.sent_to_telegram,
        "booking": {
            "details": b.details,
            "offered": [s.isoformat() for s in b.offered],
            "booked": b.booked,
            "lead_saved": b.lead_saved,
            "handoff_sent": b.handoff_sent,
        },
    }
    data = zlib.compress(json.dumps(state, separators=(",", ":")).encode(), 9)
    body = base64.urlsafe_b64encode(data).decode().rstrip("=")
    return f"{body}.{_sign(data)}"


def load(session_id: str, token: str) -> dict | None:
    """The saved state, or None if the token is missing, tampered with, too old or for another session."""
    if not token or len(token) > MAX_TOKEN_CHARS or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    try:
        data = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _sign(data)):
        return None
    try:
        state = json.loads(zlib.decompress(data))
    except (ValueError, zlib.error):
        return None
    if state.get("sid") != session_id or time.time() - state.get("issued", 0) > MAX_AGE_SECONDS:
        return None
    return state


def restore(session, state: dict) -> None:
    """Fill an empty in-memory session from a verified saved state."""
    session.messages = [m for m in state.get("messages", []) if m.get("role") in ("user", "assistant")]
    session.visitor_messages = int(state.get("visitor_messages", 0))
    session.sent_to_telegram = int(state.get("sent_to_telegram", 0))
    session.created = float(state.get("created", time.time()))
    b = state.get("booking") or {}
    session.booking = chat_booking.BookingState(
        details=b.get("details"),
        offered=[datetime.fromisoformat(s) for s in b.get("offered", [])],
        booked=bool(b.get("booked")),
        lead_saved=bool(b.get("lead_saved")),
        handoff_sent=bool(b.get("handoff_sent")),
    )
