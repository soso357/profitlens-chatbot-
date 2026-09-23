"""The chat service. Run locally with: .venv/bin/uvicorn app.main:app --reload"""
import threading
import time
from collections import deque

import anthropic
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import chat_booking, chat_log, config, guardrails, spend
from app.content import SYSTEM_PROMPT

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
SESSION_MAX_AGE_SECONDS = 24 * 3600

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ProfitLens chat")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

client = anthropic.Anthropic(max_retries=2, timeout=30.0)

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


def get_session(session_id: str) -> Session:
    now = time.time()
    with _sessions_lock:
        for sid in [s for s, v in _sessions.items() if now - v.created > SESSION_MAX_AGE_SECONDS]:
            del _sessions[sid]
        return _sessions.setdefault(session_id, Session())


class ChatIn(BaseModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")
    message: str = Field(min_length=1)


class ChatOut(BaseModel):
    reply: str
    mode: str = "chat"  # "chat", or "email_form" when the widget should show the leave your email form
    slots: list[dict] = []  # call times to show as buttons: {"start": iso, "label": text}


class BookIn(BaseModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")
    choice: str = Field(min_length=1, max_length=40)  # a slot "start", or "more" for other times


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
                    chat_booking.finish(s.booking, sid, _transcript(s), new_part)
            except Exception as e:
                chat_log.log(sid, "error", error=f"telegram digest: {e}")


threading.Thread(target=_send_quiet_conversations, daemon=True, name="telegram-digest").start()


def _reply_text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text").strip()


@app.post("/chat", response_model=ChatOut)
@limiter.limit(config.IP_RATE_LIMIT)
def chat(request: Request, body: ChatIn) -> ChatOut:
    sid = body.session_id
    session = get_session(sid)
    message = body.message.strip()

    with session.lock:
        now = time.time()
        while session.sent_times and now - session.sent_times[0] > 3600:
            session.sent_times.popleft()

        if spend.over_limit():
            chat_log.log(sid, "blocked", reason="daily spend cap reached")
            return ChatOut(reply=EMAIL_FORM_REPLY, mode="email_form")
        if len(session.sent_times) >= config.SESSION_MESSAGES_PER_HOUR:
            chat_log.log(sid, "blocked", reason="session hourly message limit")
            return ChatOut(reply=SLOW_DOWN_REPLY, mode="email_form")
        if session.visitor_messages >= config.MAX_VISITOR_MESSAGES_PER_SESSION:
            chat_log.log(sid, "blocked", reason="conversation length cap")
            return ChatOut(reply=EMAIL_FORM_REPLY, mode="email_form")
        if len(message) > config.MAX_MESSAGE_CHARS:
            chat_log.log(sid, "blocked", reason="message too long", length=len(message))
            return ChatOut(reply=TOO_LONG_REPLY)

        session.sent_times.append(now)
        session.visitor_messages += 1
        session.last_activity = now

        if guardrails.contains_card_number(message):
            message = guardrails.redact_card_numbers(message)
            chat_log.log(sid, "visitor", text=message, guardrail="card number removed")
            reply = guardrails.PAYMENT_WARNING
            if not session.messages:
                reply = guardrails.ensure_disclosure(reply)
            session.messages += [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
            chat_log.log(sid, "agent", text=reply)
            return ChatOut(reply=reply)

        chat_log.log(sid, "visitor", text=message)
        if session.booking.offered and message.strip().rstrip(".") in ("1", "2", "3"):
            reply, slots = chat_booking.pick(session.booking, message.strip().rstrip("."), sid, _transcript(session))
            session.messages += [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
            chat_log.log(sid, "agent", text=reply)
            return ChatOut(reply=reply, slots=slots)
        first_reply = not session.messages
        history = session.messages + [{"role": "user", "content": message}]

        try:
            response = client.messages.create(
                model=config.MODEL,
                max_tokens=config.MAX_REPLY_TOKENS,
                system=SYSTEM_PROMPT,
                messages=history,
                cache_control={"type": "ephemeral"},
            )
        except Exception as e:  # any failure (network, missing key, outage) still leaves the visitor a path
            chat_log.log(sid, "error", error=f"{type(e).__name__}: {e}")
            return ChatOut(reply=ERROR_REPLY, mode="email_form")

        cost = spend.cost_of(response.usage)
        spend.add(cost)

        raw = _reply_text(response)
        typed = " ".join(m["content"] for m in history if m["role"] == "user")
        text, booking_details, lead = chat_booking.extract(raw, typed)
        reply = guardrails.strip_markdown(guardrails.remove_dashes(text))
        if response.stop_reason == "max_tokens":
            reply = guardrails.trim_to_sentence(reply)

        violations = guardrails.find_violations(reply)
        if response.stop_reason == "refusal" or not reply:
            violations.append(f"no usable reply (stop reason {response.stop_reason})")
        if violations:
            chat_log.log(sid, "guardrail_blocked", reasons=violations, original=raw)
            reply, booking_details, lead = guardrails.HANDOFF_REPLY, None, None

        if first_reply:
            reply = guardrails.ensure_disclosure(reply)

        session.messages = history + [{"role": "assistant", "content": reply}]
        slots: list[dict] = []
        if booking_details and not session.booking.details:
            extra, slots = chat_booking.offer(session.booking, booking_details, sid, _transcript(session))
            reply = f"{reply} {extra}".strip()
            session.messages[-1]["content"] = reply
        if lead:
            chat_booking.record_lead(session.booking, lead, sid, _transcript(session))
        chat_log.log(
            sid, "agent", text=reply, cost_usd=round(cost, 5),
            input_tokens=response.usage.input_tokens,
            cache_read_tokens=response.usage.cache_read_input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return ChatOut(reply=reply, slots=slots)


@app.post("/book", response_model=ChatOut)
@limiter.limit(config.IP_RATE_LIMIT)
def book(request: Request, body: BookIn) -> ChatOut:
    """A time button was clicked (or "Other times")."""
    session = get_session(body.session_id)
    with session.lock:
        session.last_activity = time.time()
        reply, slots = chat_booking.pick(session.booking, body.choice, body.session_id, _transcript(session))
        clicked = "Other times, please." if body.choice == chat_booking.MORE else "(I clicked one of the call times.)"
        session.messages += [{"role": "user", "content": clicked}, {"role": "assistant", "content": reply}]
        chat_log.log(body.session_id, "agent", text=reply)
        return ChatOut(reply=reply, slots=slots)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": config.MODEL, "spent_today_usd": round(spend.spent_today(), 4),
            "daily_limit_usd": config.DAILY_SPEND_LIMIT_USD}
