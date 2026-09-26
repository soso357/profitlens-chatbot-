"""Runs every conversation in tests/conversations.md against the running local service,
scores each one, and writes the transcripts to tests/transcripts.md.

Scoring (the evals, ADR 0020): every reply must pass the code guardrails again, contain
no dashes and stay under 90 words; each conversation's "Must:", "Must not:" and "Ends in:"
lines must hold. Exit code 1 if any conversation fails.

Easiest: .venv/bin/python -m tests.evals (starts a safe local service by itself).
By hand: start .venv/bin/uvicorn app.main:app, then .venv/bin/python -m tests.run_conversations
"""
import json
import os
import re
import secrets
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = os.getenv("EVAL_BASE", "http://127.0.0.1:8000")
HERE = Path(__file__).parent
LOG = Path(os.getenv("LOG_DIR", HERE.parent / "logs")) / "conversations.jsonl"
MAX_WORDS = 90


def parse():
    convos, current = [], None
    for line in (HERE / "conversations.md").read_text().splitlines():
        if line.startswith("## "):
            current = {"title": line[3:], "expect": "", "messages": [], "must": [], "must_not": [], "ends_in": ""}
            convos.append(current)
        elif current and line.startswith("Expect:"):
            current["expect"] = line[7:].strip()
        elif current and line.startswith("V: "):
            current["messages"].append(line[3:])
        elif current and line.startswith("Must not:"):
            current["must_not"].append(line[9:].strip())
        elif current and line.startswith("Must:"):
            current["must"].append(line[5:].strip())
        elif current and line.startswith("Ends in:"):
            current["ends_in"] = line[8:].strip()
    return convos


def send(session_id, message):
    req = urllib.request.Request(
        f"{BASE}/chat", data=json.dumps({"session_id": session_id, "message": message}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def start(session_id):
    req = urllib.request.Request(
        f"{BASE}/start", data=json.dumps({"session_id": session_id}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def guardrail_events(session_id):
    if not LOG.exists():
        return []
    events = [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]
    return [e for e in events if e["session_id"] == session_id and e["event"] == "guardrail_blocked"]


def score(c, replies, last):
    """Problems found in one conversation. Empty list means it passed."""
    from app.guardrails import find_violations
    problems = []
    for n, r in enumerate(replies, 1):
        problems += [f"reply {n}: {v}" for v in find_violations(r)]
        if re.search("[\u2013\u2014]", r):
            problems.append(f"reply {n}: dash")
        if len(r.split()) > MAX_WORDS:
            problems.append(f"reply {n}: {len(r.split())} words")
    text = "\n".join(replies[1:])  # the greeting is fixed text, only the answers count
    problems += [f"missing /{p}/" for p in c["must"] if not re.search(p, text, re.I)]
    problems += [f"said /{p}/" for p in c["must_not"] if re.search(p, text, re.I)]
    ended = "slots" if last.get("slots") else last.get("mode", "chat")  # call time buttons, or the widget mode
    if c["ends_in"] and ended != c["ends_in"]:
        problems.append(f"ended in {ended!r}, expected {c['ends_in']!r}")
    return problems


def main():
    out = [f"# Test transcripts\n\nRun on {datetime.now():%Y-%m-%d %H:%M}.\n"]
    results = []
    for c in parse():
        sid = "test-" + secrets.token_hex(6)
        out.append(f"## {c['title']}\n\n*Expect: {c['expect']}*  \nSession: `{sid}`\n")
        greeting = start(sid)["reply"]
        replies, last = [greeting], {}
        out.append(f"**Agent (greeting when the chat opens):** {greeting}\n")
        for m in c["messages"]:
            r = send(sid, m)
            replies.append(r["reply"])
            last = r
            shown = "" if r["mode"] == "chat" else f"  *(widget mode: {r['mode']})*"
            slots = "".join(f"  \n  [button] {s['label']}" for s in r.get("slots", []))
            out.append(f"**Visitor:** {m}  \n**Agent:** {r['reply']}{shown}{slots}\n")
        for e in guardrail_events(sid):
            out.append(f"> Guardrail caught: {'; '.join(e['reasons'])}  \n> Original reply blocked: {e['original']}\n")
        problems = score(c, replies, last)
        results.append((c["title"], problems))
        out.append(f"**Eval: {'PASS' if not problems else 'FAIL: ' + '; '.join(problems)}**\n")
        print(f"{'PASS' if not problems else 'FAIL'}: {c['title']}" + (f" ({'; '.join(problems)})" if problems else ""))
    passed = sum(not p for _, p in results)
    out.append(f"\nScore: {passed} of {len(results)} conversations passed.\n")
    (HERE / "transcripts.md").write_text("\n".join(out))
    print(f"Score: {passed} of {len(results)} passed. Transcripts in tests/transcripts.md")
    return passed == len(results)


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
