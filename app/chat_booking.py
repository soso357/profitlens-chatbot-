"""Leads and booking inside the chat (Phases 2 and 3, spec B4, B6, B7, B11).

The model never writes call times, never says a call is booked, and never sends
alerts. It ends a reply with a hidden block and this module does the rest:

    <offer_times>{"name", "restaurant", "location", "email", "timezone"}</offer_times>
        visitor gave the four details: show three free times in their US time zone
    <lead>{"name", "restaurant", "location", "email", "reason"}</lead>
        visitor needs a founder: save the lead, alert the founders

Both blocks are removed before the visitor sees the reply.
Implements: B4, B6, B7, B11, B13
"""
import json
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app import booking, chat_log, config, email_alerts, leads, telegram

OFFER = re.compile(r"<offer_times>(.*?)</offer_times>", re.S)
LEAD = re.compile(r"<lead>(.*?)</lead>", re.S)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_LOOSE = re.compile(r"^[^@\s]+@[^@\s]+$")  # lets "maria@gmailcom" reach the typo check (B13)
YES = re.compile(r"^\s*(yes|yeah|yep|yup|y|correct|right|that'?s (it|right|correct)|sure|ok(ay)?)\b", re.I)
DEFAULT_TZ = "America/New_York"
MORE = "more"

# B13: big providers a typed domain is compared with, and real domains that look like typos of them.
PROVIDERS = ("gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "aol.com")
REAL_DOMAINS = set(PROVIDERS) | {"ymail.com", "mail.com", "email.com", "live.com", "me.com", "msn.com", "gmx.com",
                                 "aim.com", "rocketmail.com", "mac.com"}
# Common misspellings of big email providers. A typo means the invite never arrives.
EMAIL_TYPOS = {
    "gmial.com": "gmail.com", "gmal.com": "gmail.com", "gmai.com": "gmail.com", "gamil.com": "gmail.com",
    "gnail.com": "gmail.com", "gmaill.com": "gmail.com", "gmail.co": "gmail.com", "gmail.con": "gmail.com",
    "gmail.cm": "gmail.com", "gmail.om": "gmail.com", "yaho.com": "yahoo.com", "yahooo.com": "yahoo.com",
    "yahoo.co": "yahoo.com", "yahoo.con": "yahoo.com", "hotmial.com": "hotmail.com", "hotmal.com": "hotmail.com",
    "hotmail.co": "hotmail.com", "hotmail.con": "hotmail.com", "outlok.com": "outlook.com", "outlook.co": "outlook.com",
    "iclod.com": "icloud.com", "icloud.co": "icloud.com", "aol.co": "aol.com",
}

NO_TIMES_REPLY = (
    "I could not find a free time in the next two weeks. Which days and times usually work for you? "
    "A founder will email you to set it up."
)
CALENDAR_DOWN_REPLY = (
    "Sorry, I cannot reach the booking calendar right now. Which days and times usually work for you? "
    "A founder will email you to set up the call."
)
TAKEN_REPLY = "Sorry, that time was just taken. Here are the next free times:"
NOT_OFFERED_REPLY = "Please pick one of the times shown, or ask me for other times."


@dataclass
class BookingState:
    details: dict | None = None          # from <offer_times>
    offered: list[datetime] = field(default_factory=list)
    booked: bool = False
    lead_saved: bool = False             # a lead row exists for this conversation
    handoff_sent: bool = False
    pending: dict | None = None          # B13: {"kind": "offer" or "lead", "data": {...}} waiting for "yes"
    checked: list[str] = field(default_factory=list)  # B13: addresses already read back once


def _json_block(pattern: re.Pattern, raw: str) -> dict | None:
    m = pattern.search(raw)
    if not m:
        return None
    try:
        d = json.loads(m.group(1))
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


def extract(raw_reply: str, visitor_text: str = "") -> tuple[str, dict | None, dict | None]:
    """Remove hidden blocks. Returns (text for the visitor, booking details or None, lead or None).
    visitor_text: everything the visitor typed. An email is only accepted if the visitor typed it,
    so the model can never invent or guess one."""
    typed = visitor_text.lower()
    text = LEAD.sub("", OFFER.sub("", raw_reply)).strip()

    details = _json_block(OFFER, raw_reply)
    if details is not None:
        details = {k: str(details.get(k, "")).strip()[:150] for k in ("name", "restaurant", "location", "email", "timezone")}
        if (not all(details[k] for k in ("name", "restaurant", "location")) or not EMAIL_LOOSE.match(details["email"])
                or details["email"].lower() not in typed):  # no fit check: every visitor can book (B4, B5 retired)
            details = None
        elif details["timezone"] not in booking.US_TIMEZONES:
            details["timezone"] = DEFAULT_TZ

    lead = _json_block(LEAD, raw_reply)
    if lead is not None:
        lead = {k: str(lead.get(k, "")).strip()[:300] for k in ("name", "restaurant", "location", "email", "reason")}
        if not EMAIL_LOOSE.match(lead["email"]) or lead["email"].lower() not in typed:
            lead = None
    return text, details, lead


def _distance(a: str, b: str) -> int:
    """Letters to add, remove, change or swap to turn a into b (gmil to gmail is 1, gamil to gmail is 1)."""
    prev2, prev = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
            if prev2 and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[-1]


def email_check(email: str) -> tuple[bool, str | None]:
    """B13: (looks wrong, suggested address or None). Wrong means no dot after the @, or a near miss of a
    big provider: 1 letter off, or 2 for the longer names (aol.com only 1, so joe.com is left alone)."""
    user, _, domain = email.strip().rpartition("@")
    d = domain.lower()
    if not user or "." not in d.strip("."):
        return True, None
    if d in EMAIL_TYPOS:
        return True, f"{user}@{EMAIL_TYPOS[d]}"
    if d in REAL_DOMAINS:
        return False, None
    best = min(PROVIDERS, key=lambda p: _distance(d, p))
    if _distance(d, best) <= (1 if best == "aol.com" else 2):
        return True, f"{user}@{best}"
    return False, None


def email_typo(email: str) -> str | None:
    """The likely intended address if the domain looks misspelled, else None (leave your email form)."""
    return email_check(email)[1]


def handle(state: BookingState, details: dict | None, lead: dict | None, sid: str,
           transcript: str = "", source: str = "") -> tuple[str, list[dict], list[str]]:
    """Act on the hidden blocks of one reply. Returns (text to add to the reply, slots, notes).
    If the email looks wrong (B13), nothing is booked or saved; the address is read back once."""
    email = (details or lead or {}).get("email", "")
    if email:
        wrong, suggestion = email_check(email)
        # a near miss is asked about once (it may be real); an address with no dot is never accepted
        if wrong and (suggestion is None or email.lower() not in state.checked):
            state.checked.append(email.lower())
            chat_log.log(sid, "email_typo", suggestion=suggestion or "")
            if suggestion:
                state.pending = {"kind": "offer" if details else "lead", "data": {**(details or lead), "email": suggestion}}
                return (f"Just to check, did you mean {suggestion}? Reply yes, or type the right email.",
                        [], ["email looked misspelled, asked to confirm"])
            state.pending = None
            return ("That email address does not look complete. Could you type it again?",
                    [], ["email incomplete, asked again"])
    if details and not state.details:
        extra, slots = offer(state, details, sid, transcript, source)
        return extra, slots, []
    if lead and record_lead(state, lead, sid, transcript, source):
        return "", [], ["lead saved, founders alerted"]
    return "", [], []


def confirm(state: BookingState, message: str, sid: str, transcript: str = "",
            source: str = "") -> tuple[str, list[dict]] | None:
    """B13: the visitor answered a "did you mean ...?" question. "yes" uses the suggested address
    without asking the model. Anything else drops the suggestion and returns None (the model carries on)."""
    pending, state.pending = state.pending, None
    if not pending or not YES.match(message) or "@" in message:  # "yes, it is maria@gmil.com" is not a plain yes
        return None
    data = pending["data"]
    chat_log.log(sid, "email_confirmed", email=data["email"])
    if pending["kind"] == "offer":
        if state.details:
            return None
        extra, slots = offer(state, data, sid, transcript, source)
        return f"Thanks, I will use {data['email']}. {extra}", slots
    record_lead(state, data, sid, transcript, source)
    return f"Thanks, I will use {data['email']}. A founder will email you there.", []


def transcript_text(pairs) -> str:
    """pairs: iterable of (role, text) with role 'user' or 'assistant'."""
    return "\n".join(f"{'Visitor' if r == 'user' else 'Bot'}: {t}" for r, t in pairs)


def _alert(subject: str, body: str) -> None:
    telegram.send_long(f"{subject}\n{body}")
    email_alerts.alert_founders(subject, body)


def _details_text(d: dict) -> str:
    lines = [f"Name: {d.get('name') or '(not given)'}", f"Restaurant: {d.get('restaurant') or '(not given)'}",
             f"Location: {d.get('location') or '(not given)'}", f"Email: {d.get('email')}"]
    if d.get("reason"):
        lines.append(f"Needs: {d['reason']}")
    return "\n".join(lines)


def _with_chat(body: str, transcript: str) -> str:
    return body + (f"\n\nConversation:\n{transcript}" if transcript else "")


def _tag(source: str) -> str:
    return f" ({source})" if source else ""


def record_lead(state: BookingState, lead: dict, sid: str, transcript: str = "", source: str = "") -> bool:
    """Visitor needs a founder and left an email (B7). False if already done."""
    if state.handoff_sent:
        return False
    outcome = "founder needed"
    leads.save(sid, lead, outcome, source=source)
    subject = f"Chat handoff: founder needed{_tag(source)}: {lead.get('restaurant') or lead['email']}"
    _alert(subject, _with_chat(_details_text(lead), transcript))
    state.lead_saved = state.handoff_sent = True
    chat_log.log(sid, "lead_saved", outcome=outcome)
    return True


def _spread(slots: list[datetime], tz: str, count: int = 3) -> list[datetime]:
    """The earliest free time on each of the next days (visitor's calendar), so the visitor
    gets a real choice. Fills up with same day times if there are fewer free days."""
    zone = ZoneInfo(tz)
    first_per_day, seen = [], set()
    for s in slots:
        day = s.astimezone(zone).date()
        if day not in seen:
            seen.add(day)
            first_per_day.append(s)
    picked = first_per_day[:count]
    for s in slots:
        if len(picked) >= count:
            break
        if s not in picked:
            picked.append(s)
    return sorted(picked)


def _slot_list(state: BookingState, after: datetime | None = None) -> list[dict]:
    tz = (state.details or {}).get("timezone", DEFAULT_TZ)
    state.offered = _spread(booking.free_slots(60, after), tz)
    return [{"start": s.isoformat(), "label": booking.describe(s, tz)} for s in state.offered]


def _calendar_handoff(state: BookingState, sid: str, why: str, transcript: str, source: str) -> None:
    d = state.details or {}
    leads.save(sid, d, f"founder needed ({why})", source=source)
    state.lead_saved = True
    _alert(f"Chat handoff: founder needed ({why}){_tag(source)}: {d.get('restaurant', '')}",
           _with_chat(_details_text(d) + "\nPlease email them to arrange a call.", transcript))


def offer(state: BookingState, details: dict, sid: str, transcript: str = "", source: str = "") -> tuple[str, list[dict]]:
    """Returns (extra text, slots). Falls back to a founder handoff if the calendar fails (B11)."""
    state.details = details
    try:
        slots = _slot_list(state)
    except Exception as e:
        chat_log.log(sid, "error", error=f"calendar: {e}")
        _calendar_handoff(state, sid, "calendar down", transcript, source)
        return CALENDAR_DOWN_REPLY, []
    if not slots:
        _calendar_handoff(state, sid, "no free times", transcript, source)
        return NO_TIMES_REPLY, []
    chat_log.log(sid, "times_offered", slots=[s["start"] for s in slots])
    return "Here are the next free times. Pick the one that suits you:", slots


def pick(state: BookingState, choice: str, sid: str, transcript: str = "", source: str = "") -> tuple[str, list[dict]]:
    """choice: an ISO start time from a button, "1" to "3", or MORE. Returns (reply, slots)."""
    if state.booked:
        return "Your call is already booked. To change it, reply to the invite email and a founder will help.", []
    if not state.details or not state.offered:
        return NOT_OFFERED_REPLY, []
    d = state.details
    try:
        if choice == MORE:
            slots = _slot_list(state, after=state.offered[-1])
            return ("Here are some other times:", slots) if slots else (NO_TIMES_REPLY, [])
        if choice.strip() in ("1", "2", "3") and int(choice) <= len(state.offered):
            start = state.offered[int(choice) - 1]
        else:
            start = datetime.fromisoformat(choice)
            if start not in state.offered:
                return NOT_OFFERED_REPLY, []
        if not booking.is_valid_start(start):
            return TAKEN_REPLY, _slot_list(state)
        notes = f"Chat so far:\n{transcript[-1500:]}" if transcript else ""
        if source:
            notes = f"{source}\n{notes}".rstrip()
        event = booking.book(start, d["name"], d["email"], d["restaurant"], d["location"], notes=notes)
    except booking.SlotTaken:
        return TAKEN_REPLY, _slot_list(state)
    except Exception as e:
        chat_log.log(sid, "error", error=f"booking: {e}")
        _calendar_handoff(state, sid, "booking failed", transcript, source)
        return CALENDAR_DOWN_REPLY, []

    state.booked, state.offered = True, []
    when = booking.describe(start, d["timezone"])
    georgia = start.astimezone(booking.FOUNDER_TZ).strftime("%a %-d %b, %H:%M")
    leads.save(sid, d, "booked", call_time=f"{when} / {georgia} Georgia", source=source)
    state.lead_saved = True
    _alert(f"New intake call booked{_tag(source)}: {d['restaurant']}",
           _with_chat(_details_text(d) + f"\nTime: {when} / {georgia} Georgia\nMeet: {event['meet_link']}", transcript))
    chat_log.log(sid, "booked", start=start.isoformat(), restaurant=d["restaurant"])
    return (f"You are booked for {when}. A calendar invite with the Google Meet link is on its way to "
            f"{d['email']}. To change the time, just reply to that email and a founder will help."), []


def live_update(sid: str, visitor: str, reply: str, source: str = "", first: bool = False) -> None:
    """ADR 0019: mirror one exchange to the founders' Telegram group right away, in the
    background so the visitor never waits for Telegram."""
    head = f"{'New chat' if first else 'Chat'} {sid[-6:]}{_tag(source)}"
    text = f"{head}\nVisitor: {visitor}\nJelena: {reply}"
    threading.Thread(target=telegram.send_long, args=(text,), daemon=True).start()


def finish(state: BookingState, sid: str, transcript: str, new_part: str, source: str = "") -> None:
    """The conversation went quiet (or the preview ended). Send it to Telegram (ADR 0015) and
    save a visitor who saw times but did not pick one as a lead."""
    if state.details and not state.booked and not state.lead_saved:
        leads.save(sid, state.details, "times offered, not booked", source=source)
        state.lead_saved = True
        _alert(f"New lead, did not pick a time{_tag(source)}: {state.details['restaurant']}",
               _with_chat(_details_text(state.details), transcript))
    if new_part.strip() and not config.TELEGRAM_LIVE:  # with live updates the founders already saw it
        telegram.send_long(f"Chat conversation{_tag(source)} {sid[:8]}\n\n{new_part}")
    chat_log.log(sid, "conversation_sent_to_telegram")
