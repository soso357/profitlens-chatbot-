"""Offline checks of the Claude Code workflow scripts (.claude/scripts, .githooks).
Runs them in a temporary copy of the project folders, with a fake `claude` command,
so nothing real is touched and no API is called. Run: python3 -m tests.check_workflow"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / ".claude" / "scripts"
TMP = Path(tempfile.mkdtemp(prefix="profitlens-workflow-"))
(TMP / "memory" / "proposals").mkdir(parents=True)
(TMP / "memory" / "episodic" / "sessions").mkdir(parents=True)
(TMP / "docs").mkdir()
(TMP / "docs" / "plan.md").write_text("| 5 Deploy | IN PROGRESS | no |\n")
BIN = TMP / "bin"
BIN.mkdir()
FAKE = BIN / "claude"
ENV = dict(os.environ, CLAUDE_PROJECT_DIR=str(TMP), PATH=f"{BIN}:{os.environ['PATH']}")
ENV.pop("PL_WORKFLOW_SUMMARIZER", None)
STATE = TMP / "memory" / "working" / "state"
failures = 0


def check(name, ok):
    global failures
    failures += not ok
    print(f"  [{'OK' if ok else 'FAILED'}] {name}")


def script(name, stdin="", *args):
    r = subprocess.run([sys.executable, str(SCRIPTS / name), *args], input=stdin, capture_output=True, text=True,
                       env=ENV, timeout=60)
    return r.stdout


def fake_claude(ok):
    body = ("---\ntitle: Test session\nphase: Workflow\noutcome: done\nreviewed: no\n---\n\n## Goal\nx\n\n"
            "## Next steps\n1. y\n\n## Proposals\n```json\n[{\"title\": \"Idea\", \"kind\": \"test\"}]\n```\n")
    FAKE.write_text("#!/bin/sh\ncat > /dev/null\n" + (f"cat <<'X'\n{body}X\n" if ok else "echo 'Not logged in' >&2\nexit 1\n"))
    FAKE.chmod(0o755)


def transcript(path, n_user):
    with open(path, "a") as f:
        for i in range(n_user):
            f.write(json.dumps({"type": "user", "message": {"content": f"request {i}"}}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}}) + "\n")


def status(sid, pct):
    return script("statusline.py", json.dumps({"session_id": sid, "context_window": {"used_percentage": pct},
                                               "workspace": {"current_dir": str(TMP)}}))


print("Statusline and context guard:")
check("green under 60", "handoff" not in status("s1", 40))
check("yellow handoff at 64", "64% handoff" in status("s1", 64))
g1 = script("context_guard.py", json.dumps({"session_id": "s1"}))
g2 = script("context_guard.py", json.dumps({"session_id": "s1"}))
check("handoff nudge once per cycle", "CONTEXT 64%" in g1 and g2 == "")
for _ in range(3):
    out = script("session_start.py", json.dumps({"session_id": "s1", "source": "compact"}))
check("compaction counted and limit told at 3", "compaction 3 of 3" in out and "LIMIT REACHED" in out)
check("statusline STOP after 3", "STOP: 3 compactions" in status("s1", 10))
check("session limit nudge", "SESSION LIMIT" in script("context_guard.py", json.dumps({"session_id": "s1"})))

print("Session summarizer:")
tr = TMP / "t.jsonl"
transcript(tr, 1)
fake_claude(True)
check("short session skipped", "skip" in script("summarize_session.py", "", str(tr), "sid-a", "exit"))
transcript(tr, 3)
fake_claude(False)
script("summarize_session.py", "", str(tr), "sid-a", "exit")
check("failure recorded", (STATE / "sid-a.summary-failed.json").exists())
check("statusline shows failure", "summary failed" in status("s2", 10))
check("session brief shows failure", "SESSION SUMMARY FAILED" in script("session_start.py", json.dumps({"session_id": "s2"})))
fake_claude(True)
out = script("summarize_session.py", "", str(tr), "sid-a", "retry")
sessions = list((TMP / "memory" / "episodic" / "sessions").glob("*.md"))
check("retry writes the summary", "wrote" in out and len(sessions) == 1)
check("failure cleared after success", not (STATE / "sid-a.summary-failed.json").exists())
check("nothing new: resumed session not summarized again",
      "skip" in script("summarize_session.py", "", str(tr), "sid-a", "exit"))
transcript(tr, 3)
time.sleep(1.1)  # summary file names carry the second
script("summarize_session.py", "", str(tr), "sid-a", "exit")
new = sorted((TMP / "memory" / "episodic" / "sessions").glob("*.md"))
check("resumed session: only the new part, marked as a part",
      len(new) == 2 and any("part: continues" in f.read_text() for f in new))

lock = STATE / "sid-b.summary.lock"
lock.write_text("")
transcript(TMP / "b.jsonl", 3)
check("second run for the same session waits out", "another summary" in script(
    "summarize_session.py", "", str(TMP / "b.jsonl"), "sid-b", "exit"))
lock.unlink()

outs = []
threads = [threading.Thread(target=lambda i=i: outs.append(script(
    "summarize_session.py", "", str(TMP / "b.jsonl"), f"sid-p{i}", "exit"))) for i in range(3)]
[t.start() for t in threads]
[t.join() for t in threads]
nums = [p.name[:4] for p in (TMP / "memory" / "proposals").glob("[0-9]*.md")]
check("parallel runs never reuse a proposal number", len(nums) == len(set(nums)) == 5)
if len(nums) != 5:
    print("   ", sorted(nums), outs)

print("Git hooks:")
msg = TMP / "msg"
for text, want in [("[Build P5] Kill switch (R8)", 0), ("[Maintain] Summarizer lock", 0),
                   ("Merge pull request #3 from soso357/x", 0), ("Fix stuff", 1)]:
    msg.write_text(text + "\n")
    rc = subprocess.run([str(ROOT / ".githooks" / "commit-msg"), str(msg)], capture_output=True).returncode
    check(f"commit label {'accepted' if want == 0 else 'refused'}: {text}", rc == want)
for ref, want in [("refs/heads/master", 1), ("refs/heads/phase-5-kill-switch", 0)]:
    rc = subprocess.run([str(ROOT / ".githooks" / "pre-push"), "origin", "url"], input=f"refs/heads/x a {ref} b\n",
                        capture_output=True, text=True, env={k: v for k, v in os.environ.items()
                                                             if k != "ALLOW_MASTER_PUSH"}).returncode
    check(f"push to {ref} {'refused' if want else 'allowed'}", rc == want)

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
raise SystemExit(bool(failures))
