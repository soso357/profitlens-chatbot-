"""Runs every conversation in tests/conversations.md against the running local service
and writes the transcripts to tests/transcripts.md.

Start the service first: .venv/bin/uvicorn app.main:app
Then run: .venv/bin/python -m tests.run_conversations
"""
import json
import re
import secrets
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = "http://127.0.0.1:8000"
HERE = Path(__file__).parent
LOG = HERE.parent / "logs" / "conversations.jsonl"


def parse():
    convos, current = [], None
    for line in (HERE / "conversations.md").read_text().splitlines():
        if line.startswith("## "):
            current = {"title": line[3:], "expect": "", "messages": []}
            convos.append(current)
        elif current and line.startswith("Expect:"):
            current["expect"] = line[7:].strip()
        elif current and line.startswith("V: "):
            current["messages"].append(line[3:])
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


def main():
    out = [f"# Test transcripts\n\nRun on {datetime.now():%Y-%m-%d %H:%M}.\n"]
    dash_hits = 0
    for c in parse():
        sid = "test-" + secrets.token_hex(6)
        out.append(f"## {c['title']}\n\n*Expect: {c['expect']}*  \nSession: `{sid}`\n")
        out.append(f"**Agent (greeting when the chat opens):** {start(sid)['reply']}\n")
        for m in c["messages"]:
            r = send(sid, m)
            dash_hits += bool(re.search("[–—]", r["reply"]))
            mode = "" if r["mode"] == "chat" else f"  *(widget mode: {r['mode']})*"
            slots = "".join(f"  \n  [button] {s['label']}" for s in r.get("slots", []))
            out.append(f"**Visitor:** {m}  \n**Agent:** {r['reply']}{mode}{slots}\n")
        for e in guardrail_events(sid):
            out.append(f"> Guardrail caught: {'; '.join(e['reasons'])}  \n> Original reply blocked: {e['original']}\n")
        print(f"done: {c['title']}")
    out.append(f"\nReplies containing em or en dashes: {dash_hits}\n")
    (HERE / "transcripts.md").write_text("\n".join(out))
    print("Written to tests/transcripts.md")


if __name__ == "__main__":
    main()
