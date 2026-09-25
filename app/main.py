"""The chat service. Run locally with: .venv/bin/uvicorn app.main:app --reload"""
import re
import threading
import time
from collections import deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import chat_booking, chat_log, config, guardrails, leads, model, session_store, spend
from app.content import DISCLOSURE, SYSTEM_PROMPT

EMAIL_FORM_REPLY = (
    "I cannot chat right now, but a founder would be glad to help. "
    "Please leave your email and a founder will reply to you."
)
TOO_LONG_REPLY = "That message is a bit long for me. Could you send it in a shorter version?"
SLOW_DOWN_REPLY = (
    "You have sent a lot of messages in a short time. Please leave your email "
    "and a founder will pick this up with you."
)
ERROR_REPLY = (
    "Sorry, something went wrong on my side. Please leave your email "
    "and a founder will reply to you."
)
EMAIL_THANKS_REPLY = "Thank you. A founder will email you soon."
SOURCE = "LOCAL TEST" if config.TEST_PAGES else ""  # marks alerts and leads from local testing
SESSION_MAX_AGE_SECONDS = 24 * 3600
WIDGET_FILE = Path(__file__).parent / "static" / "widget.js"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ProfitLens chat")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Spec G7: only our own website may call the service from a browser.
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"])

if config.TEST_PAGES:
    from app.test_booking import router as test_booking_router
    app.include_router(test_booking_router)


class Session:
    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.sent_times: deque[float] = deque()
        self.visitor_messages = 0
        self.created = time.time()
        self.lock = threading.Lock()
        self.booking = chat_booking.BookingState()
        self.last_activity = time.time()
        self.sent_to_telegram = 0  # how many messages are already in Telegram


_sessions: dict[str, Session] = {}
_sessions_lock = threading.Lock()


def get_session(session_id: str, saved_state: str = "") -> Session:
    """The session from memory. After a restart it is rebuilt from the sealed copy the widget
    sends back (ADR 0018), so a conversation never starts over mid way."""
    now = time.time()
    with _sessions_lock:
        for sid in [s for s, v in _sessions.items() if now - v.created > SESSION_MAX_AGE_SECONDS]:
            del _sessions[sid]
        if session_id not in _sessions:
            session = Session()
            state = session_store.load(session_id, saved_state)
            if state:
                session_store.restore(session, state)
                chat_log.log(session_id, "session_restored", messages=len(session.messages))
            _sessions[session_id] = session
        return _sessions[session_id]


STATE_FIELD = Field(default="", max_length=session_store.MAX_TOKEN_CHARS)


class ChatIn(BaseModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")
    message: str = Field(min_length=1)
    state: str = STATE_FIELD  # sealed copy of the conversation (ADR 0018)


class ChatOut(BaseModel):
    reply: str
    mode: str = "chat"  # "chat", or "email_form" when the widget should show the leave your email form
    slots: list[dict] = []  # call times to show as buttons: {"start": iso, "label": text}
    state: str = ""  # sealed copy of the conversation; the widget sends it back next time


def _mirror(sid: str, session: Session, visitor: str, reply: str) -> None:
    """Every exchange to Telegram as it happens (ADR 0019)."""
    if config.TELEGRAM_LIVE:
        first = sum(1 for m in session.messages if m["role"] == "user") <= 1
        chat_booking.live_update(sid, visitor, reply, SOURCE, first)


def _out(session_id: str, session: Session, **fields) -> ChatOut:
    return ChatOut(**fields, state=session_store.dump(session_id, session))


class SessionIn(BaseModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")
    state: str = STATE_FIELD  # sealed copy of the conversation (ADR 0018)


class EmailIn(BaseModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")
    email: str = Field(max_length=200)
    note: str = Field(default="", max_length=1000)
    state: str = STATE_FIELD  # sealed copy of the conversation (ADR 0018)


class BookIn(BaseModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")
    choice: str = Field(min_length=1, max_length=40)  # a slot "start", or "more" for other times
    state: str = STATE_FIELD  # sealed copy of the conversation (ADR 0018)


def _transcript(session: Session, start: int = 0) -> str:
    return chat_booking.transcript_text((m["role"], m["content"]) for m in session.messages[start:])


def _send_quiet_conversations() -> None:
    """Every minute: conversations quiet for CONVERSATION_IDLE_MINUTES go to Telegram (ADR 0015)."""
    while True:
        time.sleep(60)
        cutoff = time.time() - config.CONVERSATION_IDLE_MINUTES * 60
        with _sessions_lock:
            due = [(sid, s) for sid, s in _sessions.items()
                   if s.last_activity < cutoff and len(s.messages) > s.sent_to_telegram]
        for sid, s in due:
            try:
                with s.lock:
                    new_part = _transcript(s, s.sent_to_telegram)
                    s.sent_to_telegram = len(s.messages)
                    chat_booking.finish(s.booking, sid, _transcript(s), new_part, SOURCE)
            except Exception as e:
                chat_log.log(sid, "error", error=f"telegram digest: {e}")


threading.Thread(target=_send_quiet_conversations, daemon=True, name="telegram-digest").start()


@app.get("/widget.js")
def widget() -> Response:
    """The whole chat widget. Framer embeds it with one script tag (Phase 4)."""
    return Response(WIDGET_FILE.read_text(encoding="utf-8"), media_type="application/javascript",
                    headers={"Cache-Control": "public, max-age=300"})


AVATAR_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}


@app.get("/avatar")
def avatar() -> Response:
    """Jelena's picture. A designer's avatar.png, .jpg or .webp in app/static wins over the placeholder SVG."""
    for ext, media in AVATAR_TYPES.items():
        f = WIDGET_FILE.parent / f"avatar{ext}"
        if f.exists():
            return Response(f.read_bytes(), media_type=media, headers={"Cache-Control": "public, max-age=3600"})
    raise HTTPException(404)


@app.post("/start", response_model=ChatOut)
@limiter.limit(config.IP_RATE_LIMIT)
def start(request: Request, body: SessionIn) -> ChatOut:
    """The widget was opened: the first message is always the AI disclosure (rule R3, set in code)."""
    sid = body.session_id
    session = get_session(sid, body.state)
    with session.lock:
        if not session.messages:
            session.messages.append({"role": "assistant", "content": DISCLOSURE})
            chat_log.log(body.session_id, "agent", text=DISCLOSURE)
        mode = "email_form" if spend.over_limit() else "chat"
        if any(m["role"] == "user" for m in session.messages):  # restored mid conversation: no second greeting
            return _out(sid, session, reply="", mode=mode)
        return _out(sid, session, reply=DISCLOSURE, mode=mode)


@app.post("/leave-email", response_model=ChatOut)
@limiter.limit(config.IP_RATE_LIMIT)
def leave_email(request: Request, body: EmailIn) -> ChatOut:
    """The leave your email form (chat unavailable, limits reached)."""
    email = body.email.strip()
    if not EMAIL.match(email):
        raise HTTPException(400, "Please check your email address.")
    sid = body.session_id
    session = get_session(sid, body.state)
    with session.lock:
        suggestion = chat_booking.email_typo(email)
        if suggestion:
            return _out(sid, session, reply=f"Just to check, did you mean {suggestion}? Please enter it again.", mode="email_form")
        lead = {"email": email, "fit": "unknown", "reason": f"left email in the form. {body.note}".strip()}
        chat_booking.record_lead(session.booking, lead, body.session_id, _transcript(session), SOURCE)
        session.messages.append({"role": "assistant", "content": EMAIL_THANKS_REPLY})
        session.last_activity = time.time()
        return _out(sid, session, reply=EMAIL_THANKS_REPLY, mode="done")


@app.post("/chat", response_model=ChatOut)
@limiter.limit(config.IP_RATE_LIMIT)
def chat(request: Request, body: ChatIn) -> ChatOut:
    sid = body.session_id
    session = get_session(sid, body.state)
    message = body.message.strip()

    with session.lock:
        now = time.time()
        while session.sent_times and now - session.sent_times[0] > 3600:
            session.sent_times.popleft()

        if spend.over_limit():
            chat_log.log(sid, "blocked", reason="daily spend cap reached")
            return _out(sid, session, reply=EMAIL_FORM_REPLY, mode="email_form")
        if len(session.sent_times) >= config.SESSION_MESSAGES_PER_HOUR:
            chat_log.log(sid, "blocked", reason="session hourly message limit")
            return _out(sid, session, reply=SLOW_DOWN_REPLY, mode="email_form")
        if session.visitor_messages >= config.MAX_VISITOR_MESSAGES_PER_SESSION:
            chat_log.log(sid, "blocked", reason="conversation length cap")
            return _out(sid, session, reply=EMAIL_FORM_REPLY, mode="email_form")
        if len(message) > config.MAX_MESSAGE_CHARS:
            chat_log.log(sid, "blocked", reason="message too long", length=len(message))
            return _out(sid, session, reply=TOO_LONG_REPLY)

        session.sent_times.append(now)
        session.visitor_messages += 1
        session.last_activity = now

        if guardrails.contains_card_number(message):
            message = guardrails.redact_card_numbers(message)
            chat_log.log(sid, "visitor", text=message, guardrail="card number removed")
            reply = guardrails.PAYMENT_WARNING
            if not any(m["role"] == "assistant" for m in session.messages):
                reply = guardrails.ensure_disclosure(reply)
            session.messages += [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
            chat_log.log(sid, "agent", text=reply)
            _mirror(sid, session, message, reply)
            return _out(sid, session, reply=reply)

        chat_log.log(sid, "visitor", text=message)
        if session.booking.offered and message.strip().rstrip(".") in ("1", "2", "3"):
            reply, slots = chat_booking.pick(session.booking, message.strip().rstrip("."), sid, _transcript(session), SOURCE)
            session.messages += [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
            chat_log.log(sid, "agent", text=reply)
            _mirror(sid, session, message, reply)
            return _out(sid, session, reply=reply, slots=slots)
        first_reply = not any(m["role"] == "assistant" for m in session.messages)
        history = session.messages + [{"role": "user", "content": message}]

        try:
            response = model.reply(SYSTEM_PROMPT, history)
        except Exception as e:  # any failure (network, missing key, outage) still leaves the visitor a path
            chat_log.log(sid, "error", error=f"{type(e).__name__}: {e}")
            _mirror(sid, session, message, "(error, visitor shown the leave your email form)")
            return _out(sid, session, reply=ERROR_REPLY, mode="email_form")

        raw = response.text
        typed = " ".join(m["content"] for m in history if m["role"] == "user")
        text, booking_details, lead = chat_booking.extract(raw, typed)
        reply = guardrails.strip_markdown(guardrails.remove_dashes(text))
        if response.stop_reason == "max_tokens":
            reply = guardrails.trim_to_sentence(reply)
        reply = guardrails.cap_length(guardrails.remove_sales_push(reply, message), message)

        violations = guardrails.find_violations(reply)
        if response.stop_reason == "refusal" or not reply:
            violations.append(f"no usable reply (stop reason {response.stop_reason})")
        if violations:
            chat_log.log(sid, "guardrail_blocked", reasons=violations, original=raw)
            reply, booking_details, lead = guardrails.HANDOFF_REPLY, None, None

        if first_reply:
            reply = guardrails.ensure_disclosure(reply)

        session.messages = history + [{"role": "assistant", "content": reply}]
        extra, slots, _ = chat_booking.handle(session.booking, booking_details, lead, sid, _transcript(session), SOURCE)
        if extra:
            reply = f"{reply} {extra}".strip()
            session.messages[-1]["content"] = reply
        chat_log.log(sid, "agent", text=reply, cost_usd=round(response.cost_usd, 5), **(response.usage or {}))
        times = "".join(f"\n  [time] {x['label']}" for x in slots)
        _mirror(sid, session, message, reply + times)
        return _out(sid, session, reply=reply, slots=slots)


@app.post("/book", response_model=ChatOut)
@limiter.limit(config.IP_RATE_LIMIT)
def book(request: Request, body: BookIn) -> ChatOut:
    """A time button was clicked (or "Other times")."""
    sid = body.session_id
    session = get_session(sid, body.state)
    with session.lock:
        session.last_activity = time.time()
        reply, slots = chat_booking.pick(session.booking, body.choice, body.session_id, _transcript(session), SOURCE)
        clicked = "Other times, please." if body.choice == chat_booking.MORE else "(I clicked one of the call times.)"
        session.messages += [{"role": "user", "content": clicked}, {"role": "assistant", "content": reply}]
        chat_log.log(sid, "agent", text=reply)
        label = "Other times" if body.choice == chat_booking.MORE else f"(clicked time {body.choice})"
        _mirror(sid, session, label, reply + "".join(f"\n  [time] {x['label']}" for x in slots))
        return _out(sid, session, reply=reply, slots=slots)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": config.MODEL, "spent_today_usd": round(spend.spent_today(), 4),
            "daily_limit_usd": config.DAILY_SPEND_LIMIT_USD}
