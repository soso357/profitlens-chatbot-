"""Offline check: broken alert channels are reported, not swallowed (proposal 0013, ADR 0021).
Fake Telegram and Gmail: nothing is sent. Run: .venv/bin/python -m tests.check_alerts"""
import os
import tempfile
from pathlib import Path

os.environ["TELEGRAM_BOT_TOKEN"] = "123456789:FAKE-token-for-tests-only-abcdefghijk"
os.environ["TELEGRAM_CHAT_ID"] = "-5552197383"
os.environ["FOUNDER_NOTIFY_EMAIL"] = "founder@example.com"

from fastapi.testclient import TestClient  # noqa: E402

from app import alert_health, config, email_alerts, telegram  # noqa: E402

TOKEN = config.TELEGRAM_BOT_TOKEN
alert_health.WARN_IN_BACKGROUND = False
config.GOOGLE_TOKEN_FILE = Path(tempfile.mkdtemp()) / "google-token.json"
config.GOOGLE_TOKEN_FILE.write_text("{}")
email_alerts._creds = lambda: None

TG, MAIL = [], []  # what reached the fake Telegram and the fake Gmail
tg_answer = {"ok": True}
tg_by_method = {}  # answers for single methods, used by the startup check tests
mail_error = None


def fake_call(method, params):
    answer = tg_by_method.get(method, tg_answer)
    if answer.get("ok"):
        TG.append((method, params.get("text", "")))
    return bool(answer.get("ok")), answer


def fake_deliver(raw):
    if mail_error:
        raise mail_error
    MAIL.append(raw)


telegram._call = fake_call
email_alerts._deliver = fake_deliver
failures = 0


def check(name, ok):
    global failures
    failures += not ok
    print(f"  [{'OK' if ok else 'FAILED'}] {name}")


def reset():
    TG.clear()
    MAIL.clear()
    alert_health._last_warned.update(telegram=0.0, email=0.0)


def mail_text():
    """Subject and body of every fake email, decoded (Gmail gets them MIME encoded)."""
    import base64
    from email import message_from_bytes, policy
    msgs = [message_from_bytes(base64.urlsafe_b64decode(m), policy=policy.default) for m in MAIL]
    return "\n".join(f"{m['Subject']}\n{m.get_content()}" for m in msgs)


print("Telegram group upgraded to a supergroup (the 2026-09-25 incident):")
reset()
tg_answer = {"ok": False, "error_code": 400, "description": "Bad Request: group chat was upgraded to a supergroup chat",
             "parameters": {"migrate_to_chat_id": -1004318522269}}
check("send reports failure", telegram.send("New lead") is False)
check("status failing", alert_health.status()["telegram"] == "failing")
check("founders emailed once", len(MAIL) == 1)
check("email names the new chat ID and the fix", "-1004318522269" in mail_text() and "TELEGRAM_CHAT_ID" in mail_text())
telegram.send("Another lead")
check("no second warning within the hour", len(MAIL) == 1)
check("token never in the reason or the email", TOKEN not in alert_health.reason("telegram") and TOKEN not in mail_text())

print("Telegram token revoked:")
reset()
tg_answer = {"ok": False, "error_code": 401, "description": "Unauthorized"}
telegram.send("x")
check("email explains the token", "BotFather" in mail_text())

print("Telegram works again:")
tg_answer = {"ok": True}
telegram.send("x")
check("status back to ok", alert_health.status()["telegram"] == "ok" and alert_health.reason("telegram") == "")

print("Recovered, then broken again within the hour:")
reset()
tg_answer = {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"}
telegram.send("x")
tg_answer = {"ok": True}
telegram.send("x")
tg_answer = {"ok": False, "error_code": 403, "description": "Forbidden: bot was kicked from the supergroup chat"}
telegram.send("x")
check("second failure after a recovery is reported at once", len(MAIL) == 2 and "profitlbot" in mail_text())

print("Email sign-in expired:")
reset()
tg_answer = {"ok": True}
mail_error = Exception("invalid_grant: Token has been expired or revoked.")
check("send reports failure", email_alerts.alert_founders("Lead", "body") is False)
check("status failing", alert_health.status()["email"] == "failing")
warn = [t for m, t in TG if m == "sendMessage"]
check("warning posted to Telegram once, with the fix", len(warn) == 1 and "google_signin.py" in warn[0])
email_alerts.alert_founders("Lead 2", "body")
check("no second warning within the hour", len([1 for m, _ in TG if m == "sendMessage"]) == 1)

print("Email settings missing:")
reset()
config.FOUNDER_NOTIFY_EMAILS = []
email_alerts.alert_founders("Lead", "body")
check("reason says FOUNDER_NOTIFY_EMAIL", "FOUNDER_NOTIFY_EMAIL" in alert_health.reason("email") and len(TG) == 1)
config.FOUNDER_NOTIFY_EMAILS = ["founder@example.com"]

print("Both broken at once:")
reset()
tg_answer = {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"}
mail_error = Exception("HttpError 500")
telegram.send("x")
check("no loop, nothing delivered, both failing", not TG and not MAIL
      and alert_health.status() == {"telegram": "failing", "email": "failing"})

print("Startup check and /health:")
reset()
tg_answer, mail_error = {"ok": True}, None
alert_health._state["telegram"]["ok"] = alert_health._state["email"]["ok"] = None
tg_by_method = {"getMe": {"ok": True, "result": {"id": 42}},
                "getChatMember": {"ok": True, "result": {"status": "administrator"}}}
check("startup check posts nothing to the group",
      telegram.check() and [m for m, _ in TG] == ["getChat", "getMe", "getChatMember"])
check("startup email check sends nothing", email_alerts.check() and MAIL == [])
for member, chat_perm, name in [({"status": "restricted", "can_send_messages": False}, True, "restricted bot"),
                                ({"status": "member"}, False, "group lets only admins post"),
                                ({"status": "left"}, True, "bot removed")]:
    reset()
    tg_by_method = {"getMe": {"ok": True, "result": {"id": 42}}, "getChatMember": {"ok": True, "result": member},
                    "getChat": {"ok": True, "result": {"permissions": {"can_send_messages": chat_perm}}}}
    check(f"startup check catches: {name}", telegram.check() is False and "cannot post" in mail_text())
tg_by_method = {}
alert_health._state["telegram"]["ok"] = True
from app import main  # noqa: E402

body = TestClient(main.app).get("/health").json()
check("/health shows alerts ok", body.get("alerts") == {"telegram": "ok", "email": "ok"})
tg_answer = {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"}
telegram.send("x")
body = TestClient(main.app).get("/health").text
check("/health shows failing without the reason", '"telegram":"failing"' in body and "chat not found" not in body)

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
raise SystemExit(bool(failures))
