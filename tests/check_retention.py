"""Offline check: conversation log lines older than 30 days are deleted (R9, ADR 0027).
Works on a temporary folder, never on the real logs. Run: .venv/bin/python -m tests.check_retention
"""
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

TMP = Path(tempfile.mkdtemp())
os.environ["LOG_DIR"] = str(TMP)

from app import chat_log, config  # noqa: E402

results = []


def check(name, ok):
    results.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name)


def line(days_ago, sid):
    t = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return json.dumps({"time": t.isoformat(timespec="seconds"), "session_id": sid, "event": "visitor"}) + "\n"


def sessions():
    return [json.loads(x)["session_id"] for x in chat_log._FILE.read_text().splitlines()]


check("test uses a temporary folder, not the real logs", config.LOG_DIR == TMP and chat_log._FILE.parent == TMP)
check("missing log is fine", chat_log.delete_old() == 0)

chat_log._FILE.write_text("")
check("empty log is fine", chat_log.delete_old() == 0 and chat_log._FILE.read_text() == "")

chat_log._FILE.write_text(line(31, "old") + "not json\n" + line(29, "recent") + line(0, "today"))
deleted = chat_log.delete_old()
check("31 day old line and unreadable line deleted", deleted == 2 and sessions() == ["recent", "today"])
check("running again deletes nothing", chat_log.delete_old() == 0 and sessions() == ["recent", "today"])

chat_log.log("new", "visitor", text="hello")
check("a message written after cleanup is kept", sessions() == ["recent", "today", "new"])

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)} of {len(results)} passed")
raise SystemExit(1 if failed else 0)
