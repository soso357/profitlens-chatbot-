"""Offline checks of booking inside the chat (app/chat_booking.py). No calendar, no alerts sent.
Run: .venv/bin/python -m tests.check_booking"""
from datetime import datetime, timedelta

from app import booking, chat_booking as cb

SENT = []
cb.telegram.send = lambda text: SENT.append(("telegram", text)) or True
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
        '"location": "Austin, TX", "email": "maria@example.com", "timezone": "America/Chicago", "fit": "fit"}</offer_times>')
results = []


def check(name, ok):
    results.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name)


text, d = cb.extract(GOOD)
check("hidden block removed from visible text", "<offer_times>" not in text and text == "Great, here are the times.")
check("details read", d is not None and d["restaurant"] == "Casa Maria" and d["timezone"] == "America/Chicago")
check("no block means no booking", cb.extract("Hello there.")[1] is None)
check("bad email means no booking", cb.extract(GOOD.replace("maria@example.com", "not an email"))[1] is None)
check("not a fit means no booking (B5)", cb.extract(GOOD.replace('"fit": "fit"', '"fit": "not fit"'))[1] is None)
check("unclear fit still books", cb.extract(GOOD.replace('"fit": "fit"', '"fit": "unclear"'))[1] is not None)
check("unknown time zone falls back to Eastern",
      cb.extract(GOOD.replace("America/Chicago", "Mars/Base"))[1]["timezone"] == "America/New_York")
check("broken block is ignored and hidden", cb.extract("Hi <offer_times>{oops</offer_times>") == ("Hi", None))

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

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)} of {len(results)} passed")
raise SystemExit(1 if failed else 0)
