"""Offline checks of leads and booking inside the chat (app/chat_booking.py).
No calendar, no alerts sent, leads written to a temporary file.
Run: .venv/bin/python -m tests.check_booking"""
import csv
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from app import booking, chat_booking as cb, leads, telegram

SENT = []
TG_RAW = []
telegram.send = lambda text: TG_RAW.append(text) or True
cb.telegram.send_long = lambda text: SENT.append(("telegram", text)) or True
leads.FILE = Path(tempfile.mkdtemp()) / "leads.csv"
cb.email_alerts.alert_founders = lambda subject, body: SENT.append(("email", subject)) or True
cb.chat_log.log = lambda *a, **k: None

BASE = datetime(2026, 10, 1, 19, 0, tzinfo=booking.FOUNDER_TZ)
FREE = [BASE + timedelta(minutes=30 * i) for i in range(9)]
BOOKED = []


def fake_free_slots(count=3, after=None):
    return [s for s in FREE if after is None or s > after][:count]


def fake_book(start, name, email, restaurant, location, notes=""):
    BOOKED.append((start, email, notes))
    return {"id": "x", "meet_link": "https://meet.google.com/test", "calendar_link": ""}


booking.free_slots = fake_free_slots
booking.is_valid_start = lambda s: True
booking.book = fake_book

GOOD = ('Great, here are the times.\n<offer_times>{"name": "Maria", "restaurant": "Casa Maria", '
        '"location": "Austin, TX", "email": "maria@example.com", "timezone": "America/Chicago"}</offer_times>')
results = []


def check(name, ok):
    results.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name)


TYPED = "maria@example.com bob@example.com"
text, d, _ = cb.extract(GOOD, TYPED)
check("hidden block removed from visible text", "<offer_times>" not in text and text == "Great, here are the times.")
check("details read", d is not None and d["restaurant"] == "Casa Maria" and d["timezone"] == "America/Chicago")
check("no block means no booking", cb.extract("Hello there.")[1] is None)
check("bad email means no booking", cb.extract(GOOD.replace("maria@example.com", "not an email"), TYPED)[1] is None)
BAR = GOOD.replace("Casa Maria", "Bob's Bar").replace("maria@example.com", "bob@example.com")
check("a bar owner with the four details gets times (B4, B5 retired)", cb.extract(BAR, TYPED)[1] is not None)
check("an old style fit field is ignored, still books",
      cb.extract(GOOD.replace('"timezone"', '"fit": "not fit", "timezone"'), TYPED)[1] is not None)
check("missing restaurant means no booking (B4)", cb.extract(GOOD.replace('"Casa Maria"', '""'), TYPED)[1] is None)
check("unknown time zone falls back to Eastern",
      cb.extract(GOOD.replace("America/Chicago", "Mars/Base"), TYPED)[1]["timezone"] == "America/New_York")
check("broken block is ignored and hidden", cb.extract("Hi <offer_times>{oops</offer_times>") == ("Hi", None, None))

s = cb.BookingState()
extra, slots = cb.offer(s, d, "t")
check("three times offered", len(slots) == 3 and "Central time" in slots[0]["label"])
check("times contain no dashes (R4)", not any(ch in sl["label"] for sl in slots for ch in "–—"))
reply, more = cb.pick(s, cb.MORE, "t")
check("other times are later ones", len(more) == 3 and more[0]["start"] > slots[-1]["start"])
reply, _ = cb.pick(s, (BASE - timedelta(days=3)).isoformat(), "t")
check("a time that was never offered is refused", reply == cb.NOT_OFFERED_REPLY and not BOOKED)
expected = s.offered[1]
reply, _ = cb.pick(s, "2", "t", transcript="Visitor: hi", source="TEST")
check("typing 2 books the second time shown", len(BOOKED) == 1 and BOOKED[0][0] == expected)
check("confirmation names the email and Meet", "maria@example.com" in reply and "Meet" in reply)
check("founders alerted by Telegram and email", any(k == "telegram" and "booked" in t for k, t in SENT) and any(k == "email" for k, _ in SENT))
reply, _ = cb.pick(s, "1", "t")
check("no second booking", len(BOOKED) == 1 and "already booked" in reply)

s2 = cb.BookingState()
booking.free_slots = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("calendar down"))
SENT.clear()
reply, slots = cb.offer(s2, d, "t")
check("calendar down: apology and no times (B11)", reply == cb.CALENDAR_DOWN_REPLY and not slots)
check("calendar down: founder handoff alert", any("founder needed" in t for _, t in SENT))

s3 = cb.BookingState()
booking.free_slots = fake_free_slots
cb.offer(s3, d, "t")
booking.book = lambda *a, **k: (_ for _ in ()).throw(booking.SlotTaken())
reply, slots = cb.pick(s3, "1", "t")
check("time just taken: new times offered", reply == cb.TAKEN_REPLY and len(slots) == 3)

def rows():
    return list(csv.DictReader(leads.FILE.open())) if leads.FILE.exists() else []


check("booking saved a 'booked' lead, calendar down saved a handoff lead",
      [r["outcome"] for r in rows()] == ["booked", "founder needed (calendar down)"])

# Phase 2: handoff leads
LEAD = ('Thanks, a founder will email you.\n<lead>{"name": "Bob", "restaurant": "Bob Bar", "location": "Miami, FL", '
        '"email": "bob@example.com", "reason": "asks about a discount"}</lead>')
text, det, lead = cb.extract(LEAD, TYPED)
check("lead block hidden from visitor", text == "Thanks, a founder will email you." and det is None and lead is not None)
check("lead without a valid email is ignored", cb.extract(LEAD.replace("bob@example.com", "bob"), TYPED)[2] is None)
check("invented email (visitor never typed it) is refused", cb.extract(LEAD, "maria@example.com")[2] is None)
check("invented email refused for booking too", cb.extract(GOOD, "bob@example.com")[1] is None)
s4 = cb.BookingState()
SENT.clear()
cb.record_lead(s4, lead, "s4", transcript="Visitor: any discount?")
check("handoff lead saved", rows()[-1]["outcome"] == "founder needed" and rows()[-1]["email"] == "bob@example.com")
check("handoff alert has the conversation, no fit line", any("any discount?" in t and "Fit:" not in t for k, t in SENT if k == "telegram"))
cb.record_lead(s4, lead, "s4")
check("same conversation alerts only once", len([r for r in rows() if r["session_id"] == "s4"]) == 1)
_, _, h = cb.extract(LEAD, TYPED)
s5 = cb.BookingState()
SENT.clear()
cb.record_lead(s5, h, "s5")
check("handoff subject is 'Chat handoff: founder needed' (B7)", any(k == "email" and t.startswith("Chat handoff: founder needed") for k, t in SENT))

# visitor saw times, never picked, conversation went quiet (old digest mode, ADR 0015)
cb.config.TELEGRAM_LIVE = False
s6 = cb.BookingState()
cb.offer(s6, d, "s6")
SENT.clear()
cb.finish(s6, "s6", "Visitor: hi\nBot: times", "Visitor: hi\nBot: times")
check("unpicked times saved as a lead", rows()[-1]["outcome"] == "times offered, not booked")
check("conversation sent to Telegram when quiet (ADR 0015)", any(t.startswith("Chat conversation") for k, t in SENT if k == "telegram"))
SENT.clear()
cb.finish(cb.BookingState(), "s7", "Visitor: hi", "Visitor: hi")
check("anonymous chat also goes to Telegram, no lead", len(SENT) == 1 and rows()[-1]["session_id"] != "s7")

# live mode (ADR 0019): the quiet check only saves the lead, the chat was already mirrored
cb.config.TELEGRAM_LIVE = True
s9 = cb.BookingState()
cb.offer(s9, d, "s9")
SENT.clear()
cb.finish(s9, "s9", "Visitor: hi", "Visitor: hi")
check("live mode: quiet check saves the lead, no second copy of the chat", rows()[-1]["session_id"] == "s9"
      and not any(t.startswith("Chat conversation") for k, t in SENT if k == "telegram"))
import time as _t
LIVE = []
cb.telegram.send_long = lambda text: LIVE.append(text) or True
cb.live_update("abc123456789", "How much is it?", "It is $99.", first=True)
_t.sleep(0.3)
check("live mode: each exchange goes to Telegram right away", LIVE and LIVE[0].startswith("New chat 456789")
      and "Visitor: How much is it?" in LIVE[0] and "Jelena: It is $99." in LIVE[0])

# long conversations are split for Telegram
TG_RAW.clear()
del cb.telegram.send_long
import importlib
importlib.reload(telegram)
telegram.send = lambda text: TG_RAW.append(text) or True
telegram.send_long("\n".join("line %d %s" % (i, "x" * 80) for i in range(200)))
check("long text split into Telegram sized parts", len(TG_RAW) > 1 and all(len(t) <= 4096 for t in TG_RAW))

# email typos (invite would never arrive)
check("gmial.com is caught", cb.email_typo("tekola@gmial.com") == "tekola@gmail.com")
check("a correct address passes", cb.email_typo("maria@example.com") is None and cb.email_typo("x@gmail.com") is None)
s8 = cb.BookingState()
typo_details = dict(d, email="maria@gmial.com")
extra, slots, notes = cb.handle(s8, typo_details, None, "s8")
check("typo: no times, visitor asked to retype", "maria@gmail.com" in extra and not slots and s8.details is None)
extra, slots, _ = cb.handle(s8, d, None, "s8")
check("after retyping, times are offered", len(slots) == 3)

# B13: near misses read back once, "yes" uses the suggestion, no dot asks again
for addr, want in [("maria@gmil.com", "maria@gmail.com"), ("maria@gamil.com", "maria@gmail.com"),
                   ("maria@yhoo.com", "maria@yahoo.com"), ("maria@outlok.com", "maria@outlook.com"),
                   ("maria@hotmil.com", "maria@hotmail.com")]:
    check(f"B13 {addr} suggests {want}", cb.email_check(addr) == (True, want))
for addr in ("maria@ymail.com", "maria@mail.com", "maria@live.com", "joe@joe.com", "maria@mariaskitchen.com",
             "x@gmail.co.uk", "x@aol.com", "x@yahoo.ca", "x@outlook.cl", "x@hotmail.fr"):
    check(f"B13 {addr} is left alone", cb.email_check(addr) == (False, None))
check("B13 no dot after @ looks wrong, no suggestion", cb.email_check("maria@gmailcom") == (True, None))
TYPED13 = TYPED + " maria@gmil.com maria@gmailcom"
_, d13, _ = cb.extract(GOOD.replace("maria@example.com", "maria@gmil.com"), TYPED13)
s13 = cb.BookingState()
extra, slots, _ = cb.handle(s13, d13, None, "s13")
check("B13 gmil.com: read back, no times yet", "did you mean maria@gmail.com? Reply yes" in extra and not slots
      and s13.pending and s13.details is None)
reply, slots = cb.confirm(s13, "Yes", "s13")
check("B13 yes: times offered with gmail.com", len(slots) == 3 and s13.details["email"] == "maria@gmail.com"
      and "maria@gmail.com" in reply and s13.pending is None)
s14 = cb.BookingState()
cb.handle(s14, d13, None, "s14")
check("B13 'yes, gmil.com is correct' is not a plain yes", cb.confirm(s14, "yes, gmil.com is correct", "s14") is None
      and s14.pending is not None)
extra, slots, _ = cb.handle(s14, d13, None, "s14")
check("B13 while waiting, the unconfirmed address is never booked", not slots and "did you mean maria@gmail.com" in extra)
check("B13 retyping an address clears the question", cb.confirm(s14, "it is maria@gmil.com", "s14") is None
      and s14.pending is None)
extra, slots, _ = cb.handle(s14, d13, None, "s14")
check("B13 same near miss typed again is accepted (asked once)", len(slots) == 3 and s14.details["email"] == "maria@gmil.com")
for said in ("Oh yes, sorry", "Yea", "yess", "absolutely"):
    s17 = cb.BookingState()
    cb.handle(s17, d13, None, "s17")
    got = cb.confirm(s17, said, "s17")
    check(f"B13 '{said}' counts as yes", got is not None and s17.details["email"] == "maria@gmail.com")
check("B13 form keeps the old list only (yahoo.ca, hotmeal.com pass)", cb.email_typo("x@yahoo.ca") is None
      and cb.email_typo("x@hotmeal.com") is None and cb.email_typo("x@gmial.com") == "x@gmail.com")
_, dnd, _ = cb.extract(GOOD.replace("maria@example.com", "maria@gmailcom"), TYPED13)
s15 = cb.BookingState()
check("B13 no dot reaches the check", dnd is not None)
extra, slots, _ = cb.handle(s15, dnd, None, "s15")
extra2, slots2, _ = cb.handle(s15, dnd, None, "s15")
check("B13 no dot: asked to type again, every time, never booked", "does not look complete" in extra
      and "does not look complete" in extra2 and not slots and not slots2 and s15.details is None)
_, _, l16 = cb.extract(LEAD.replace("bob@example.com", "bob@gmil.com"), TYPED + " bob@gmil.com")
s16 = cb.BookingState()
cb.handle(s16, None, l16, "s16")
SENT.clear()
reply, _ = cb.confirm(s16, "yep", "s16", transcript="Visitor: any discount?")
check("B13 handoff lead: yes saves it with gmail.com", rows()[-1]["email"] == "bob@gmail.com" and "founder" in reply)
_, _, l18 = cb.extract(LEAD.replace("bob@example.com", "bob@gmil.com"), TYPED + " bob@gmil.com")
extra, _, _ = cb.handle(s16, None, l18, "s16")
check("B13 after a handoff was sent, no new read back or false promise", extra == "" and s16.pending is None)

# times spread over different days
from zoneinfo import ZoneInfo
day1 = [BASE + timedelta(minutes=30 * i) for i in range(6)]
day2 = [BASE + timedelta(days=1, minutes=30 * i) for i in range(6)]
day4 = [BASE + timedelta(days=3)]
picked = cb._spread(day1 + day2 + day4, "America/Chicago")
check("three times on three different days", len({p.astimezone(ZoneInfo("America/Chicago")).date() for p in picked}) == 3)
check("earliest time is still first", picked[0] == day1[0])
check("one free day only: fills with same day times", cb._spread(day1, "America/Chicago") == day1[:3])

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)} of {len(results)} passed")
raise SystemExit(1 if failed else 0)
