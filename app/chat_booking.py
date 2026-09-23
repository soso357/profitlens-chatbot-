"""Booking inside the chat (Phase 3, spec B6 and B11).

The model never writes call times and never says a call is booked. When it has the
visitor's details and a fit result, it ends its reply with a hidden block:

    <offer_times>{"name": "...", "restaurant": "...", "location": "...",
                  "email": "...", "timezone": "America/Chicago", "fit": "fit"}</offer_times>

This module strips that block, reads the calendar, and returns up to three times
in the visitor's US time zone. Booking a picked time happens only here, in code.
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime

from app import booking, chat_log, email_alerts, telegram

MARKER = re.compile(r"<offer_times>(.*?)</offer_times>", re.S)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_TZ = "America/New_York"
MORE = "more"

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
    details: dict | None = None
    offered: list[datetime] = field(default_factory=list)
    booked: bool = False


def extract(raw_reply: str) -> tuple[str, dict | None]:
    """Remove the hidden block. Returns (text for the visitor, details or None)."""
    m = MARKER.search(raw_reply)
    text = MARKER.sub("", raw_reply).strip()
    if not m:
        return text, None
    try:
        d = json.loads(m.group(1))
    except ValueError:
        return text, None
    details = {k: str(d.get(k, "")).strip()[:150] for k in ("name", "restaurant", "location", "email", "timezone", "fit")}
    if not all(details[k] for k in ("name", "restaurant", "location")) or not EMAIL.match(details["email"]):
        return text, None
    if details["timezone"] not in booking.US_TIMEZONES:
        details["timezone"] = DEFAULT_TZ
    if details["fit"] not in ("fit", "unclear"):
        return text, None  # not a fit: no booking (B5)
    return text, details


def _slot_list(state: BookingState, after: datetime | None = None) -> list[dict]:
    state.offered = booking.free_slots(3, after)
    tz = (state.details or {}).get("timezone", DEFAULT_TZ)
    return [{"start": s.isoformat(), "label": booking.describe(s, tz)} for s in state.offered]


def _alert(subject: str, lines: str) -> None:
    telegram.send(f"{subject}\n{lines}")
    email_alerts.alert_founders(subject, lines)


def _details_text(d: dict) -> str:
    return (f"Name: {d['name']}\nRestaurant: {d['restaurant']}\nLocation: {d['location']}\n"
            f"Email: {d['email']}\nFit: {d['fit']}")


def offer(state: BookingState, details: dict, sid: str) -> tuple[str, list[dict]]:
    """Returns (extra text, slots). Falls back to a founder handoff if the calendar fails (B11)."""
    state.details = details
    try:
        slots = _slot_list(state)
    except Exception as e:
        chat_log.log(sid, "error", error=f"calendar: {e}")
        _alert(f"Chat handoff: founder needed (calendar down): {details['restaurant']}",
               _details_text(details) + "\nThe calendar could not be read. Please email them to arrange a call.")
        return CALENDAR_DOWN_REPLY, []
    if not slots:
        _alert(f"Chat handoff: founder needed (no free times): {details['restaurant']}", _details_text(details))
        return NO_TIMES_REPLY, []
    chat_log.log(sid, "times_offered", slots=[s["start"] for s in slots])
    return "Here are the next free times. Pick the one that suits you:", slots


def pick(state: BookingState, choice: str, sid: str, transcript: str = "", source: str = "") -> tuple[str, list[dict]]:
    """choice: an ISO start time from a button, "1" to "3", or MORE. Returns (reply, slots)."""
    if state.booked:
        return "Your call is already booked. To change it, reply to the invite email and a founder will help.", []
    if not state.details or not state.offered:
        return NOT_OFFERED_REPLY, []
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
        d = state.details
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
        if state.details:
            _alert(f"Chat handoff: founder needed (booking failed): {state.details['restaurant']}",
                   _details_text(state.details) + "\nBooking failed. Please email them to arrange a call.")
        return CALENDAR_DOWN_REPLY, []

    state.booked, state.offered = True, []
    when = booking.describe(start, d["timezone"])
    georgia = start.astimezone(booking.FOUNDER_TZ).strftime("%a %-d %b, %H:%M")
    _alert(f"New intake call booked{' (' + source + ')' if source else ''}: {d['restaurant']}",
           _details_text(d) + f"\nTime: {when} / {georgia} Georgia\nMeet: {event['meet_link']}")
    chat_log.log(sid, "booked", start=start.isoformat(), restaurant=d["restaurant"])
    return (f"You are booked for {when}. A calendar invite with the Google Meet link is on its way to "
            f"{d['email']}. To change the time, just reply to that email and a founder will help."), []
