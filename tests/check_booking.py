"""Offline checks of leads inside the chat (app/chat_booking.py, ADR 0032: no call booking).
No alerts sent, leads written to a temporary file.
Run: .venv/bin/python -m tests.check_booking"""
import csv
import tempfile
import time
from pathlib import Path

from app import chat_booking as cb, leads, telegram

SENT = []
TG_RAW = []
ORIG_SEND_LONG = telegram.send_long
telegram.send = lambda text: TG_RAW.append(text) or True
cb.telegram.send_long = lambda text: SENT.append(("telegram", text)) or True
leads.FILE = Path(tempfile.mkdtemp()) / "leads.csv"
cb.email_alerts.alert_founders = lambda subject, body: SENT.append(("email", subject)) or True
cb.chat_log.log = lambda *a, **k: None

results = []


def check(name, ok):
    results.append((name, bool(ok)))
    print(f"  [{'OK' if ok else 'FAILED'}] {name}")


def rows():
    with leads.FILE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


TYPED = "Hi, I am Bob from Bob Bar in Florida. bob@example.com"
LEAD = ('A founder will email you to set up the call.\n<lead>{"name": "Bob", "restaurant": "Bob Bar", '
        '"location": "FL", "email": "bob@example.com", "reason": "wants the intake call"}</lead>')

# hidden block and what the visitor sees
text, lead = cb.extract(LEAD, TYPED)
check("lead block hidden from visitor", text == "A founder will email you to set up the call." and lead is not None)
check("no block means no lead", cb.extract("Hello there.")[1] is None)
check("lead without a valid email is ignored", cb.extract(LEAD.replace("bob@example.com", "bob"), TYPED)[1] is None)
check("invented email (visitor never typed it) is refused", cb.extract(LEAD, "maria@example.com")[1] is None)
check("broken block is ignored and hidden", cb.extract("Hi <lead>{oops</lead>") == ("Hi", None))
check("no call time is ever shown in the reply", "[time]" not in LEAD and "time" not in cb.extract(LEAD, TYPED)[0].lower().split("set up")[0])

# the lead is saved and the founders are alerted once
s4 = cb.BookingState()
SENT.clear()
extra = cb.handle(s4, lead, "s4", transcript="Visitor: I want the call")
check("intake lead saved", rows()[-1]["outcome"] == "founder needed" and rows()[-1]["email"] == "bob@example.com")
check("founder alert has the conversation", any("I want the call" in t for k, t in SENT if k == "telegram"))
check("founder alert by email too, subject is handoff", any(k == "email" and t.startswith("Chat handoff: founder needed") for k, t in SENT))
check("no extra text added to the reply", extra == "")
n = len(rows())
cb.handle(s4, lead, "s4")
check("same conversation saves only once", len(rows()) == n)

# email typos (invite would never arrive)
check("gmial.com is caught", cb.email_typo("tekola@gmial.com") == "tekola@gmail.com")
check("a correct address passes", cb.email_typo("maria@example.com") is None and cb.email_typo("x@gmail.com") is None)

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
_, l13 = cb.extract(LEAD.replace("bob@example.com", "maria@gmil.com"), TYPED13)
s13 = cb.BookingState()
SENT.clear()
extra = cb.handle(s13, l13, "s13")
check("B13 gmil.com: read back, nothing saved yet", "did you mean maria@gmail.com? Reply yes" in extra
      and s13.pending is not None and not any(r["email"] == "maria@gmil.com" for r in rows()))
reply = cb.confirm(s13, "Yes", "s13")
check("B13 yes: saved with gmail.com", reply and "maria@gmail.com" in reply and s13.pending is None
      and rows()[-1]["email"] == "maria@gmail.com")

s14 = cb.BookingState()
cb.handle(s14, l13, "s14")
check("B13 'yes, gmil.com is correct' is not a plain yes", cb.confirm(s14, "yes, gmil.com is correct", "s14") is None
      and s14.pending is not None)
extra = cb.handle(s14, l13, "s14")
check("B13 while waiting, the unconfirmed address is never saved", "did you mean maria@gmail.com" in extra
      and not any(r["email"] == "maria@gmil.com" for r in rows()))
check("B13 retyping an address clears the question", cb.confirm(s14, "it is maria@gmil.com", "s14") is None
      and s14.pending is None)
cb.handle(s14, l13, "s14")
check("B13 same near miss typed again is accepted (asked once)", rows()[-1]["email"] == "maria@gmil.com")

for said in ("Oh yes, sorry", "Yea", "yess", "absolutely"):
    s17 = cb.BookingState()
    cb.handle(s17, l13, "s17")
    got = cb.confirm(s17, said, "s17")
    check(f"B13 '{said}' counts as yes", got is not None and rows()[-1]["email"] == "maria@gmail.com")

_, lno = cb.extract(LEAD.replace("bob@example.com", "maria@gmailcom"), TYPED13)
s15 = cb.BookingState()
extra = cb.handle(s15, lno, "s15")
extra2 = cb.handle(s15, lno, "s15")
check("B13 no dot: asked to type again, every time, never saved", "does not look complete" in extra
      and "does not look complete" in extra2 and not any(r["email"] == "maria@gmailcom" for r in rows()))

_, l16 = cb.extract(LEAD.replace("bob@example.com", "bob@gmil.com"), TYPED + " bob@gmil.com")
s16 = cb.BookingState()
cb.handle(s16, l16, "s16")
reply = cb.confirm(s16, "yep", "s16", transcript="Visitor: any discount?")
check("B13 lead: yes saves it with gmail.com", rows()[-1]["email"] == "bob@gmail.com" and "founder" in (reply or ""))
extra = cb.handle(s16, l16, "s16")
check("B13 after a handoff was sent, no new read back", extra == "" and s16.pending is None)

# live mode (ADR 0019) and the quiet-conversation digest (ADR 0015)
cb.config.TELEGRAM_LIVE = False
SENT.clear()
cb.finish("s7", "Visitor: hi\nBot: hello")
check("quiet conversation goes to Telegram (ADR 0015)", any(t.startswith("Chat conversation") for k, t in SENT if k == "telegram"))

cb.config.TELEGRAM_LIVE = True
LIVE = []
cb.telegram.send_long = lambda text: LIVE.append(text) or True
cb.live_update("abc123456789", "How much is it?", "It is $99.", first=True)
time.sleep(0.3)
check("live mode: each exchange goes to Telegram right away", LIVE and LIVE[0].startswith("New chat 456789")
      and "Visitor: How much is it?" in LIVE[0] and "Jelena: It is $99." in LIVE[0])

# long conversations are split for Telegram
TG_RAW.clear()
ORIG_SEND_LONG("\n".join("line %d %s" % (i, "x" * 80) for i in range(200)))
check("long text split into Telegram sized parts", len(TG_RAW) > 1 and all(len(t) <= 4096 for t in TG_RAW))

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)} of {len(results)} passed")
raise SystemExit(1 if failed else 0)
