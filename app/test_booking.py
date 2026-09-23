"""Local test page for trying the booking step as a client. Only mounted when TEST_PAGES=1."""
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app import booking, chat_log, email_alerts, telegram

router = APIRouter()
PAGE = Path(__file__).parent / "static" / "test-booking.html"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.get("/test-booking", response_class=HTMLResponse)
def page() -> str:
    return PAGE.read_text(encoding="utf-8")


@router.get("/test-chat", response_class=HTMLResponse)
def chat_page() -> str:
    return (Path(__file__).parent / "static" / "test-chat.html").read_text(encoding="utf-8")


@router.get("/api/slots")
def slots(tz: str = "America/New_York", after: str | None = None) -> dict:
    if tz not in booking.US_TIMEZONES:
        raise HTTPException(400, "unknown time zone")
    try:
        found = booking.free_slots(3, datetime.fromisoformat(after) if after else None)
    except Exception as e:
        chat_log.log("test-booking", "error", error=f"calendar: {e}")
        raise HTTPException(503, "calendar unavailable")
    return {"slots": [{"start": s.isoformat(), "label": booking.describe(s, tz)} for s in found]}


class BookIn(BaseModel):
    start: str
    tz: str
    name: str = Field(min_length=1, max_length=100)
    restaurant: str = Field(min_length=1, max_length=150)
    location: str = Field(min_length=1, max_length=150)
    email: str = Field(max_length=200)


@router.post("/api/book")
def book(body: BookIn) -> dict:
    if not EMAIL.match(body.email) or body.tz not in booking.US_TIMEZONES:
        raise HTTPException(400, "Please check your email address.")
    start = datetime.fromisoformat(body.start)
    if not booking.is_valid_start(start):
        raise HTTPException(400, "That time is no longer available. Please pick another.")
    try:
        event = booking.book(start, body.name, body.email, body.restaurant, body.location,
                             notes="TEST booking from the local test page.")
    except booking.SlotTaken:
        raise HTTPException(409, "Sorry, that time was just taken. Please pick another.")
    except Exception as e:
        chat_log.log("test-booking", "error", error=f"booking: {e}")
        raise HTTPException(503, "Sorry, booking is not working right now. A founder will email you.")

    when = booking.describe(start, body.tz)
    georgia = start.astimezone(booking.FOUNDER_TZ).strftime("%a %-d %b, %H:%M")
    alert = (
        f"Name: {body.name}\nRestaurant: {body.restaurant}\nLocation: {body.location}\nEmail: {body.email}\n"
        f"Time: {when} / {georgia} Georgia\nMeet: {event['meet_link']}"
    )
    telegram.send(f"New intake call booked (TEST)\n{alert}")
    email_alerts.alert_founders(f"New intake call (TEST): {body.restaurant}", alert)
    chat_log.log("test-booking", "booked", start=start.isoformat(), restaurant=body.restaurant, email=body.email)
    return {"when": when, "meet_link": event["meet_link"]}


@router.get("/widget-test", response_class=HTMLResponse)
def widget_test(demo: str = "") -> str:
    """A stand in for a useprofitlens.com page with the widget embedded exactly like Framer will.
    ?demo=open opens the chat; ?demo=ask also sends a first question (for screenshots)."""
    auto = ""
    if demo:
        auto = """<script>
window.addEventListener("load", function () { setTimeout(function () {
  var r = document.getElementById("profitlens-chat").shadowRoot;
  r.querySelector(".launcher").click();
  if ("%s" === "ask") setTimeout(function () {
    var i = r.querySelector("input"); i.value = "Hi, what is ProfitLens and how much does it cost?";
    r.querySelector("form").requestSubmit();
  }, 1500);
}, 300); });
</script>""" % demo
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Widget test</title>
<style>body{{margin:0;font-family:Geist,-apple-system,sans-serif;color:#666;background:#fafafa}}
section{{max-width:720px;margin:0 auto;padding:80px 24px}}h1{{color:#111;font-size:40px;margin:0 0 16px}}</style></head>
<body><section><h1>Know what every dish really costs you.</h1>
<p>This is a local stand in for the ProfitLens website. The chat button in the bottom right corner is the real widget,
loaded with the same one line embed Framer will use.</p></section>
<script src="/widget.js" defer></script>{auto}</body></html>"""


@router.get("/widget-phone", response_class=HTMLResponse)
def widget_phone(demo: str = "open") -> str:
    """The widget test page inside a phone sized frame (390 x 844, like an iPhone)."""
    return f"""<!doctype html><html><body style="margin:0;background:#ddd">
<iframe src="/widget-test?demo={demo}" style="width:390px;height:844px;border:0;background:#fff;display:block"></iframe>
</body></html>"""
