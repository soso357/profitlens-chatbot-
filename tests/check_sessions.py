"""Offline check: a conversation survives a server restart (ADR 0018). No API calls, no alerts.
Run: .venv/bin/python -m tests.check_sessions"""
import os
from datetime import datetime, timezone

os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["FOUNDER_NOTIFY_EMAIL"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app import chat_booking, main, model, session_store  # noqa: E402

SEEN = []


def fake_reply(system, history):
    SEEN.append([m["content"] for m in history])
    return model.Reply(text="Is your restaurant open right now?", stop_reason="end_turn")


main.model.reply = fake_reply
client = TestClient(main.app)
results = []


def check(name, ok):
    results.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name)


SID = "sessiontest0001"
r = client.post("/start", json={"session_id": SID}).json()
token = r["state"]
check("greeting comes with a sealed copy", r["reply"].startswith("Hi, I'm Jelena") and "." in token)
r = client.post("/chat", json={"session_id": SID, "message": "My name is Nino", "state": token}).json()
token = r["state"]

main._sessions.clear()  # the server restarts: memory is gone

r = client.post("/chat", json={"session_id": SID, "message": "food", "state": token}).json()
check("after the restart the model still sees the earlier messages", "My name is Nino" in SEEN[-1])
check("no second introduction after the restart", "Jelena" not in r["reply"] and r["reply"] == "Is your restaurant open right now?")

main._sessions.clear()
bad = token[:-3] + ("AAA" if not token.endswith("AAA") else "BBB")
client.post("/chat", json={"session_id": SID, "message": "hello", "state": bad})
check("a tampered copy is ignored (conversation not restored)", "My name is Nino" not in SEEN[-1])

main._sessions.clear()
client.post("/chat", json={"session_id": "othersession01", "message": "hello", "state": r["state"]})
check("a copy from another session is ignored", "My name is Nino" not in SEEN[-1])

# booking state survives too (times on screen, then a restart, then the click)
s = main.Session()
s.messages = [{"role": "assistant", "content": "hi"}]
s.booking.details = {"name": "Nino", "restaurant": "Nino's", "location": "Austin, TX",
                     "email": "nino@example.com", "timezone": "America/Chicago"}
s.booking.offered = [datetime(2026, 10, 1, 15, 0, tzinfo=timezone.utc)]
s.booking.pending = {"kind": "offer", "data": {"email": "nino@gmail.com"}}
s.booking.checked = ["nino@gmil.com"]
tok = session_store.dump("bookingtest01", s)
s2 = main.Session()
loaded = session_store.load("bookingtest01", tok)
assert loaded is not None
session_store.restore(s2, loaded)
check("offered call times and visitor details survive", s2.booking.offered == s.booking.offered
      and s2.booking.details["email"] == "nino@example.com" and isinstance(s2.booking, chat_booking.BookingState))
check("B13 pending email suggestion survives a restart", s2.booking.pending == {"kind": "offer", "data": {"email": "nino@gmail.com"}}
      and s2.booking.checked == ["nino@gmil.com"])
check("sealed copy stays small", len(tok) < 2000)

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)} of {len(results)} passed")
raise SystemExit(1 if failed else 0)
