"""Reads free times from the founders' Google Calendar and books intake calls.
Implements: B6
"""
import threading
import uuid
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app import config

FOUNDER_TZ = ZoneInfo(config.BOOKING_TIMEZONE)
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

US_TIMEZONES = {
    "America/New_York": "Eastern",
    "America/Chicago": "Central",
    "America/Denver": "Mountain",
    "America/Phoenix": "Arizona",
    "America/Los_Angeles": "Pacific",
    "America/Anchorage": "Alaska",
    "Pacific/Honolulu": "Hawaii",
}

_book_lock = threading.Lock()


def _calendar():
    creds = Credentials.from_authorized_user_file(str(config.GOOGLE_TOKEN_FILE))
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _parse_hhmm(value: str) -> time:
    h, m = value.split(":")
    return time(int(h), int(m))


def _candidate_starts(from_utc: datetime, to_utc: datetime):
    """Every possible call start inside the founders' working hours, in order."""
    start_t, end_t = _parse_hhmm(config.BOOKING_START), _parse_hhmm(config.BOOKING_END)
    window = (datetime.combine(datetime.min, end_t) - datetime.combine(datetime.min, start_t)) % timedelta(days=1)
    step = timedelta(minutes=config.SLOT_STEP_MINUTES)
    length = timedelta(minutes=config.CALL_MINUTES)
    day = from_utc.astimezone(FOUNDER_TZ).date() - timedelta(days=1)
    while True:
        opens = datetime.combine(day, start_t, tzinfo=FOUNDER_TZ)
        if opens > to_utc:
            return
        if DAYS[day.weekday()] in config.BOOKING_DAYS:
            s = opens
            while s + length <= opens + window:
                if from_utc <= s <= to_utc:
                    yield s
                s += step
        day += timedelta(days=1)


def _busy(cal, from_utc: datetime, to_utc: datetime):
    result = cal.freebusy().query(body={
        "timeMin": from_utc.isoformat(), "timeMax": to_utc.isoformat(),
        "items": [{"id": config.GOOGLE_CALENDAR_ID}],
    }).execute()["calendars"][config.GOOGLE_CALENDAR_ID]
    if result.get("errors"):
        raise RuntimeError(f"calendar not readable: {result['errors']}")
    return [(datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])) for b in result["busy"]]


def _is_free(start: datetime, busy) -> bool:
    end = start + timedelta(minutes=config.CALL_MINUTES)
    return not any(start < b_end and end > b_start for b_start, b_end in busy)


def free_slots(count: int = 3, after: datetime | None = None) -> list[datetime]:
    """The next free call times (founder time zone), at most `count`."""
    now = datetime.now(timezone.utc)
    earliest = now + timedelta(hours=config.BOOKING_MIN_NOTICE_HOURS)
    if after and after + timedelta(minutes=1) > earliest:
        earliest = after + timedelta(minutes=1)
    latest = now + timedelta(days=config.BOOKING_HORIZON_DAYS)
    if earliest >= latest:
        return []
    busy = _busy(_calendar(), earliest, latest + timedelta(hours=1))
    slots = []
    for s in _candidate_starts(earliest, latest):
        if _is_free(s, busy):
            slots.append(s)
            if len(slots) == count:
                break
    return slots


def is_valid_start(start: datetime) -> bool:
    """True if `start` is one of the times the calendar would offer."""
    now = datetime.now(timezone.utc)
    if not now + timedelta(hours=config.BOOKING_MIN_NOTICE_HOURS) <= start <= now + timedelta(days=config.BOOKING_HORIZON_DAYS):
        return False
    return any(s == start for s in _candidate_starts(start - timedelta(minutes=1), start + timedelta(minutes=1)))


class SlotTaken(Exception):
    pass


def book(start: datetime, name: str, email: str, restaurant: str, location: str, notes: str = "") -> dict:
    """Creates the call with a Meet link and the visitor as guest. Google emails the invite."""
    with _book_lock:
        cal = _calendar()
        end = start + timedelta(minutes=config.CALL_MINUTES)
        if not _is_free(start, _busy(cal, start - timedelta(minutes=1), end + timedelta(minutes=1))):
            raise SlotTaken()
        event = cal.events().insert(
            calendarId=config.GOOGLE_CALENDAR_ID, conferenceDataVersion=1, sendUpdates="all",
            body={
                "summary": f"ProfitLens intake call: {restaurant}",
                "description": (
                    f"Booked by the ProfitLens website chat assistant.\n\n"
                    f"Name: {name}\nRestaurant: {restaurant}\nLocation: {location}\nEmail: {email}\n"
                    + (f"\n{notes}\n" if notes else "")
                    + "\nTo reschedule, reply to the founder's email. The chat assistant does not reschedule."
                ),
                "start": {"dateTime": start.isoformat()},
                "end": {"dateTime": end.isoformat()},
                "attendees": [{"email": email, "displayName": name}],
                "conferenceData": {"createRequest": {
                    "requestId": uuid.uuid4().hex, "conferenceSolutionKey": {"type": "hangoutsMeet"}}},
                "reminders": {"useDefault": True},
            },
        ).execute()
    return {"id": event["id"], "meet_link": event.get("hangoutLink", ""), "calendar_link": event.get("htmlLink", "")}


def describe(start: datetime, tz_name: str) -> str:
    local = start.astimezone(ZoneInfo(tz_name))
    return f"{local:%A %-d %B, %-I:%M %p} {US_TIMEZONES.get(tz_name, tz_name)} time"
