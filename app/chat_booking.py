"""Leads and booking inside the chat (Phases 2 and 3, spec B5, B6, B7, B11).

The model never writes call times, never says a call is booked, and never sends
alerts. It ends a reply with a hidden block and this module does the rest:

    <offer_times>{"name", "restaurant", "location", "email", "timezone", "fit": "fit|unclear"}</offer_times>
        visitor fits: show three free times in their US time zone
    <lead>{"name", "restaurant", "location", "email", "fit": "not fit|unknown", "reason"}</lead>
        visitor does not fit, or needs a founder: save the lead, alert the founders

Both blocks are removed before the visitor sees the reply.
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app import booking, chat_log, email_alerts, leads, telegram

OFFER = re.compile(r"<offer_times>(.*?)</offer_times>", re.S)
LEAD = re.compile(r"<lead>(.*?)</lead>", re.S)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_TZ = "America/New_York"
MORE = "more"

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
        details = {k: str(details.get(k, "")).strip()[:150] for k in ("name", "restaurant", "location", "email", "timezone", "fit")}
        if (not all(details[k] for k in ("name", "restaurant", "location")) or not EMAIL.match(details["email"])
                or details["email"].lower() not in typed or details["fit"] not in ("fit", "unclear")):  # not a fit never gets times (B5)
            details = None
        elif details["timezone"] not in booking.US_TIMEZONES:
            details["timezone"] = DEFAULT_TZ

    lead = _json_block(LEAD, raw_reply)
    if lead is not None:
        lead = {k: str(lead.get(k, "")).strip()[:300] for k in ("name", "restaurant", "location", "email", "fit", "reason")}
        if not EMAIL.match(lead["email"]) or lead["email"].lower() not in typed:
            lead = None
    return text, details, lead


def email_typo(email: str) -> str | None:
    """The likely intended address if the domain is a common misspelling, else None."""
    user, _, domain = email.rpartition("@")
    fixed = EMAIL_TYPOS.get(domain.lower())
    return f"{user}@{fixed}" if fixed else None


def handle(state: BookingState, details: dict | None, lead: dict | None, sid: str,
           transcript: str = "", source: str = "") -> tuple[str, list[dict], list[str]]:
    """Act on the hidden blocks of one reply. Returns (text to add to the reply, slots, notes).
    If the email looks misspelled, nothing is booked or saved; the visitor is asked to check it."""
    email = (details or lead or {}).get("email", "")
    suggestion = email_typo(email) if email else None
    if suggestion:
        chat_log.log(sid, "email_typo", suggestion=suggestion)
        return (f"Just to check, did you mean {suggestion}? Please type your email again so the invite reaches you.",
                [], ["email looked misspelled, asked again"])
    if details and not state.details:
        extra, slots = offer(state, details, sid, transcript, source)
        return extra, slots, []
    if lead and record_lead(state, lead, sid, transcript, source):
        return "", [], ["lead saved, founders alerted"]
    return "", [], []


def transcript_text(pairs) -> str:
    """pairs: iterable of (role, text) with role 'user' or 'assistant'."""
    return "\n".join(f"{'Visitor' if r == 'user' else 'Bot'}: {t}" for r, t in pairs)


def _alert(subject: str, body: str) -> None:
    telegram.send_long(f"{subject}\n{body}")
    email_alerts.alert_founders(subject, body)


def _details_text(d: dict) -> str:
    lines = [f"Name: {d.get('name') or '(not given)'}", f"Restaurant: {d.get('restaurant') or '(not given)'}",
             f"Location: {d.get('location') or '(not given)'}", f"Email: {d.get('email')}", f"Fit: {d.get('fit') or 'unknown'}"]
    if d.get("reason"):
        lines.append(f"Needs: {d['reason']}")
    return "\n".join(lines)


def _with_chat(body: str, transcript: str) -> str:
    return body + (f"\n\nConversation:\n{transcript}" if transcript else "")


def _tag(source: str) -> str:
    return f" ({source})" if source else ""


def record_lead(state: BookingState, lead: dict, sid: str, transcript: str = "", source: str = "") -> bool:
    """Visitor does not fit or needs a founder, and left an email (B5, B7). False if already done."""
    if state.handoff_sent:
        return False
    not_fit = lead.get("fit") == "not fit"
    outcome = "not a fit" if not_fit else "founder needed"
    leads.save(sid, lead, outcome, source=source)
    subject = (f"New lead, not a fit{_tag(source)}: {lead.get('restaurant') or lead['email']}" if not_fit
               else f"Chat handoff: founder needed{_tag(source)}: {lead.get('restaurant') or lead['email']}")
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
        notes = f"Fit result: {d['fit']}" + (f"\n\nChat so far:\n{transcript[-1500:]}" if transcript else "")
        if source:
            notes = f"{source}\n{notes}"
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


def finish(state: BookingState, sid: str, transcript: str, new_part: str, source: str = "") -> None:
    """The conversation went quiet (or the preview ended). Send it to Telegram (ADR 0015) and
    save a fit visitor who saw times but did not pick one as a lead."""
    if state.details and not state.booked and not state.lead_saved:
        leads.save(sid, state.details, "times offered, not booked", source=source)
        state.lead_saved = True
        _alert(f"New lead, did not pick a time{_tag(source)}: {state.details['restaurant']}",
               _with_chat(_details_text(state.details), transcript))
    if new_part.strip():
        telegram.send_long(f"Chat conversation{_tag(source)} {sid[:8]}\n\n{new_part}")
    chat_log.log(sid, "conversation_sent_to_telegram")
