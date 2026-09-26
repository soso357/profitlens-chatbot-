"""Offline checks of the Claude Code workflow scripts (.claude/scripts, .githooks).
Runs them in a temporary copy of the project folders, with a fake `claude` command,
so nothing real is touched and no API is called. Run: python3 -m tests.check_workflow"""
import fcntl
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
sys.path.insert(0, str(SCRIPTS))
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
            "## Next steps\n1. y\n\n## Proposals\n```json\n[{\"title\": \"Idea PID\", \"kind\": \"test\"}]\n```\n")
    # PID becomes the process id: every run gets a different title, so parallel runs cannot share a file name
    FAKE.write_text("#!/bin/sh\ncat > /dev/null\n" + (f"cat <<'X' | sed \"s/PID/$$/\"\n{body}X\n" if ok else "echo 'Not logged in' >&2\nexit 1\n"))
    FAKE.chmod(0o755)


def transcript(path, n_user):
    with open(path, "a") as f:
        for i in range(n_user):
            f.write(json.dumps({"type": "user", "message": {"content": f"request {i}"}}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}}) + "\n")


def status(sid, pct):
    return script("statusline.py", json.dumps({"session_id": sid, "context_window": {"used_percentage": pct},
                                               "workspace": {"current_dir": str(TMP)}}))


print("Statusline and context guard (ADR 0022):")
check("green under 60", "handoff" not in status("s1", 40) and "new terminal" not in status("s1", 40))
check("yellow handoff at 64", "64% handoff" in status("s1", 64))
g1 = script("context_guard.py", json.dumps({"session_id": "s1"}))
g2 = script("context_guard.py", json.dumps({"session_id": "s1"}))
check("handoff nudge once per cycle", "CONTEXT 64%" in g1 and "task's handoff" in g1 and g2 == "")
check("red new terminal at 72", "72% new terminal" in status("s1", 72))
g3 = script("context_guard.py", json.dumps({"session_id": "s1"}))
g4 = script("context_guard.py", json.dumps({"session_id": "s1"}))
check("soft stop once at 70", "time for a new session" in g3 and "soft" in g3 and g4 == "")
status("s9", 75)
g9 = script("context_guard.py", json.dumps({"session_id": "s9"}))
check("jump straight to 75: stop, not the 60 nudge", "time for a new session" in g9 and "CONTEXT 75%: before" not in g9)
check("compaction only at 85 (settings)", json.loads((ROOT / ".claude" / "settings.json").read_text())
      ["env"]["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] == "85")

print("Task handoffs (ADR 0022):")
start = script("session_start.py", json.dumps({"session_id": "s3", "source": "startup"}))
check("new session loads nothing, one line", "nothing loaded" in start and "Plan status" not in start
      and "proposals" not in start and len(start) < 400)
HO = TMP / "memory" / "working" / "handoffs"
HO.mkdir(parents=True, exist_ok=True)


def handoff(slug, branch, status="open", updated="2026-09-26 10:00"):
    f = HO / f"{slug}.md"
    head = f"branch: {branch}\n" if branch else ""
    f.write_text(f"---\ntask: {slug}\ntype: Build\n{head}updated: {updated}\nstatus: {status}\n---\n\n"
                 f"## Goal\nGOAL-{slug}\n")
    return f


a = handoff("task-a", None, updated="2026-09-26 10:00")
b = handoff("task-b", "branch-b", updated="2026-09-26 11:00")
handoff("task-old", "branch-c", status="done")
script("handoff_track.py", json.dumps({"session_id": "s4", "tool_name": "Write", "tool_input": {"file_path": str(a)}}))
check("writing a handoff records the session's task", json.loads((STATE / "s4.json").read_text()).get("task") == "task-a")
idx = (HO / "_index.md").read_text()
check("index rebuilt with open and done tasks", "task-a" in idx and "task-old" in idx and "done" in idx)
lst = script("handoffs.py", "", "list")
check("list: open only, newest first", lst.index("task-b") < lst.index("task-a") and "task-old" not in lst)
c = script("session_start.py", json.dumps({"session_id": "s4", "source": "compact", "cwd": str(TMP)}))
check("compaction reinjects this session's own task, not the newer one",
      "GOAL-task-a" in c and "GOAL-task-b" not in c and "new terminal" in c)
check("statusline shows the task and 'compacted'", "task task-a" in status("s4", 20) and "compacted" in status("s4", 20))
check("new terminal nudge after a compaction", "SESSION WAS COMPACTED" in script(
    "context_guard.py", json.dumps({"session_id": "s4"})))
script("pre_compact.py", json.dumps({"session_id": "s5", "trigger": "auto"}))
c5 = script("session_start.py", json.dumps({"session_id": "s5", "source": "compact", "cwd": str(TMP)}))
check("no own task: falls back to this session's snapshot, never another task",
      "Auto snapshot" in c5 and "GOAL-" not in c5)
check("path command gives a slug in the handoffs folder",
      script("handoffs.py", "", "path", "Phase 5: Kill switch!").strip() == str(HO / "phase-5-kill-switch.md"))
brief = script("handoffs.py", "", "brief")
check("resume brief has tasks and phase status", "task-b" in brief and "Phase status" in brief)

print("Worktree shares the main folder's memory (ADR 0023 C2):")
repo = TMP / "repo"
repo.mkdir()
git = lambda *a, cwd=repo: subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, timeout=30,
                                         stdin=subprocess.DEVNULL)
git("init", "-q", "-b", "master")
(repo / "x").write_text("x")
git("add", "x")
git("-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "[Maintain] x")
git("worktree", "add", "-q", str(TMP / "wt"), "-b", "maintain-wt")
wt_home = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import common; "
                          "print(common.HANDOFFS)", str(SCRIPTS)], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                         env=dict(ENV, CLAUDE_PROJECT_DIR=str(TMP / "wt"))).stdout.strip()
check("handoffs resolved to the main folder from a worktree",
      Path(wt_home).resolve() == (repo / "memory" / "working" / "handoffs").resolve())
WT_ENV = dict(ENV, CLAUDE_PROJECT_DIR=str(TMP / "wt"))
WHO = repo / "memory" / "working" / "handoffs"
WHO.mkdir(parents=True)


def track(sid, f, cwd):
    subprocess.run([sys.executable, str(SCRIPTS / "handoff_track.py")], env=WT_ENV, capture_output=True, text=True,
                   input=json.dumps({"session_id": sid, "cwd": str(cwd), "tool_input": {"file_path": str(f)}}))
    try:
        return json.loads((repo / "memory" / "working" / "state" / f"{sid}.json").read_text()).get("task")
    except Exception:
        return None


for slug, br, st in (("own", "maintain-wt", "open"), ("other", "phase-9-x", "open"), ("closed", "maintain-wt", "done")):
    (WHO / f"{slug}.md").write_text(f"---\ntask: {slug}\ntype: Build\nbranch: {br}\nstatus: {st}\n---\n")
check("writing an open handoff on this session's branch claims it", track("w1", WHO / "own.md", TMP / "wt") == "own")
check("writing another terminal's handoff (other branch) does not claim it", track("w2", WHO / "other.md", TMP / "wt") is None)
check("closing a task (status done) does not claim it", track("w3", WHO / "closed.md", TMP / "wt") is None)
fake_claude(True)
transcript(TMP / "wt.jsonl", 3)
r = subprocess.run([sys.executable, str(SCRIPTS / "summarize_session.py"), str(TMP / "wt.jsonl"), "sid-wt", "exit"],
                   env=WT_ENV, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
check("summary written from a worktree lands in the main folder, no false failure",
      "wrote" in r.stdout and list((repo / "memory" / "episodic" / "sessions").glob("*sid-wt*"))
      and not (repo / "memory" / "working" / "state" / "sid-wt.summary-failed.json").exists())

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
from summarize_session import close_header  # noqa: E402
check("unclosed summary header gets closed", close_header("---\ntitle: x\nreviewed: yes\n\n## Goal\ny")
      == "---\ntitle: x\nreviewed: yes\n\n---\n## Goal\ny" and close_header("---\na: b\n---\n\n## G") == "---\na: b\n---\n\n## G")
check("summary header closed and readable", all("reviewed" in __import__("common").frontmatter(f)[0] for f in sessions))
check("nothing new: resumed session not summarized again",
      "skip" in script("summarize_session.py", "", str(tr), "sid-a", "exit"))
transcript(tr, 3)
time.sleep(1.1)  # summary file names carry the second
script("summarize_session.py", "", str(tr), "sid-a", "exit")
new = sorted((TMP / "memory" / "episodic" / "sessions").glob("*.md"))
check("resumed session: only the new part, marked as a part",
      len(new) == 2 and any("part: continues" in f.read_text() for f in new))

held = open(STATE / "sid-b.summary.lock", "w")
fcntl.flock(held, fcntl.LOCK_EX)
transcript(TMP / "b.jsonl", 3)
check("second run for the same session waits out", "another summary" in script(
    "summarize_session.py", "", str(TMP / "b.jsonl"), "sid-b", "exit"))
held.close()
check("lock left by a finished run does not block", "wrote" in script(
    "summarize_session.py", "", str(TMP / "b.jsonl"), "sid-b", "exit"))

outs = []
threads = [threading.Thread(target=lambda i=i: outs.append(script(
    "summarize_session.py", "", str(TMP / "b.jsonl"), f"sid-p{i}", "exit"))) for i in range(4)]
[t.start() for t in threads]
[t.join() for t in threads]
nums = [p.name[:4] for p in (TMP / "memory" / "proposals").glob("[0-9]*.md")]
check("parallel runs with different titles never reuse a proposal number", len(nums) == len(set(nums)) == 7)
if len(nums) != 7:
    print("   ", sorted(nums), outs)

print("Summaries sorted into project files (step 2):")
PROG = TMP / "docs" / "progress.md"
PROG.write_text("# Progress\n\n## Done (newest first)\n\n- 2026-09-01: Old thing done.\n\n## Open questions\n\n"
                "- Who pays for the Render plan? (Ioseb)\n\n## Waiting on people\n\n- Founders: approve the test page.\n")
(TMP / "docs" / "build-log.md").write_text("- 2026-09-26: Ioseb chose soft stop at 70 percent for context.\n")
(TMP / "memory" / "procedural").mkdir(parents=True, exist_ok=True)
LES = TMP / "memory" / "procedural" / "lessons.md"
LES.write_text("# Lessons\n\n- 2026-09-22: Scripted edits must fail loudly when the old text is not found.\n")
PLAN_BEFORE = (TMP / "docs" / "plan.md").read_text()
SUMS = TMP / "memory" / "episodic" / "sessions"


def routed_summary(name, routed):
    f = SUMS / name
    f.write_text("---\ntitle: t\nreviewed: no\n---\n\n## Next steps\n1. x\n\n## Routed\n```json\n"
                 + (routed if isinstance(routed, str) else json.dumps(routed)) + "\n```\n")
    return f


def distribute(f):
    return json.loads(script("distribute.py", "", str(f)).strip().splitlines()[-1])


nprops = len(list((TMP / "memory" / "proposals").glob("[0-9]*.md")))
r = distribute(routed_summary("2026-09-26-100000-aaaa.md", {
    "done": ["Kill switch built and tested (pull request #4)"],
    "open_questions": [{"question": "Should call times be spread over different days?", "who": "Ioseb"},
                       {"question": "Who pays for the Render plan?", "who": "Ioseb"}],
    "waiting": [{"who": "Ioseb", "what": "buy a new Anthropic API key"}],
    "decisions": [{"decision": "context stop", "chosen": "soft stop at 70 percent", "by": "Ioseb"},
                  {"decision": "Widget colour", "chosen": "dark green launcher button", "by": "founders"}],
    "lessons": ["Scripted edits must fail loudly when old text is not found", "Render env changes need a manual redeploy"],
    "changes": [{"file": "spec", "what": "Add a rule for visitors writing in Spanish", "why": "a visitor did"}]}))
prog = PROG.read_text()
done_part = prog.split("## Done (newest first)")[1].split("## ")[0]
check("done item added at the top of Done, with its source", done_part.strip().startswith(
    "- 20") and "Kill switch built" in done_part.strip().splitlines()[0] and "(from 2026-09-26-100000-aaaa.md)" in prog)
check("new open question added, known one not added twice", "spread over different days" in prog
      and prog.count("Render plan") == 1)
check("waiting item added under Waiting on people", "new Anthropic API key" in prog.split("## Waiting on people")[1])
les = LES.read_text()
check("new lesson appended with source, repeated lesson not appended", "manual redeploy" in les
      and les.count("fail loudly") == 1)
titles = [__import__("common").frontmatter(f)[0].get("title", "") for f in sorted((TMP / "memory" / "proposals")
                                                                                    .glob("[0-9]*.md"))[nprops:]]
from common import similar  # noqa: E402
check("different numbers are different items", not similar("Step 1 merged (pull request #3)",
                                                           "Step 2 merged (pull request #4)"))
check("same item reworded is the same", similar("- 2026-09-20: Kill switch built and tested (from a.md)",
                                                "The kill switch was built and tested"))
check("repeated lesson becomes a rule proposal", any(x.startswith("Make a rule") for x in titles))
check("decision missing from build log becomes a proposal, logged one does not",
      any("Widget colour" in x for x in titles) and not any("context stop" in x for x in titles))
check("spec change becomes a proposal; plan.md untouched", any(x.startswith("Change spec") for x in titles)
      and (TMP / "docs" / "plan.md").read_text() == PLAN_BEFORE)
before = PROG.read_text()
r2 = distribute(routed_summary("2026-09-26-110000-bbbb.md", {
    "done": ["Kill switch built and tested (pull request #4)"], "changes": [
        {"file": "spec", "what": "Add a rule for visitors writing in Spanish", "why": "again"}]}))
check("same items again: nothing added, no duplicate proposal", PROG.read_text() == before and r2["proposals"] == [])
r3 = distribute(routed_summary("2026-09-26-120000-cccc.md", "{not json"))
check("broken Routed block: nothing changed, failure kept for the brief", PROG.read_text() == before
      and r3["ok"] is False and "failed" in script("handoffs.py", "", "brief"))
check("summary without a Routed block is fine", distribute(SUMS / "2026-09-26-100000-aaaa.md")["ok"])
fs = [routed_summary(f"2026-09-26-13000{i}-par{i}.md", {"done": [f"Parallel result number {i} zebra{i} finished"]})
      for i in range(4)]
procs = [subprocess.Popen([sys.executable, str(SCRIPTS / "distribute.py"), str(f)], env=ENV, stdout=subprocess.DEVNULL,
                          stdin=subprocess.DEVNULL) for f in fs]
[x.wait(timeout=60) for x in procs]
prog = PROG.read_text()
check("four summaries sorted at once: all four kept, file intact", all(f"zebra{i}" in prog for i in range(4))
      and prog.count("## Done") == 1 and prog.count("## Open questions") == 1)

print("Staleness (step 2):")
SEM = TMP / "memory" / "semantic"
SEM.mkdir(parents=True, exist_ok=True)
(SEM / "old.md").write_text("---\ntitle: Old facts\nlast_verified: 2026-01-01\n---\nbody\n")
(SEM / "fresh.md").write_text(f"---\ntitle: Fresh\nlast_verified: {time.strftime('%Y-%m-%d')}\n---\nbody\n")
(TMP / "memory" / "proposals" / "0900-deferred-idea.md").write_text(
    "---\ntitle: Deferred idea\nstatus: deferred\ncreated: 2026-01-01\n---\n\n## Decision\nIoseb, 2026-01-02: deferred.\n")
b = script("handoffs.py", "", "brief")
check("brief flags old semantic memory, not fresh", "old.md" in b and "fresh.md" not in b)
check("brief lists a deferred proposal that is due", "Deferred idea" in b)
handoff("finished-long-ago", None, status="done", updated="2026-01-01 10:00")
handoff("finished-today", None, status="done", updated=time.strftime("%Y-%m-%d %H:%M"))
script("handoffs.py", "", "index")
check("done handoff older than 14 days deleted, recent one kept",
      not (HO / "finished-long-ago.md").exists() and (HO / "finished-today.md").exists())

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
