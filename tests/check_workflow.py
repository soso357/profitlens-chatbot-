"""Offline checks of the Claude Code workflow scripts (.claude/scripts, .githooks).
Runs them in a temporary copy of the project folders,
so nothing real is touched. Run: python3 -m tests.check_workflow"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / ".claude" / "scripts"
sys.path.insert(0, str(SCRIPTS))
TMP = Path(tempfile.mkdtemp(prefix="profitlens-workflow-"))
(TMP / "memory" / "proposals").mkdir(parents=True)
(TMP / "docs").mkdir()
(TMP / "docs" / "plan.md").write_text("| 5 Deploy | IN PROGRESS | no |\n")
ENV = dict(os.environ, CLAUDE_PROJECT_DIR=str(TMP))
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
print("Staleness (step 2):")
SEM = TMP / "memory" / "semantic"
SEM.mkdir(parents=True, exist_ok=True)
(SEM / "old.md").write_text("---\ntitle: Old facts\nlast_verified: 2026-01-01\n---\nbody\n")
(SEM / "fresh.md").write_text(f"---\ntitle: Fresh\nlast_verified: {time.strftime('%Y-%m-%d')}\n---\nbody\n")
(TMP / "memory" / "proposals" / "0900-deferred-idea.md").write_text(
    "---\ntitle: Deferred idea\nstatus: deferred\ncreated: 2026-01-01\n---\n\n## Decision\nIoseb, 2026-01-02: deferred.\n")
(TMP / "memory" / "proposals" / "0902-deferred-no-date.md").write_text(
    "---\ntitle: Undated deferral\nstatus: deferred\ncreated: 2026-01-01\n---\n\n## Decision\n(pending Ioseb)\n"
    "Deferred: wait until Phase 6.\n")
(TMP / "memory" / "proposals" / "0903-deferred-again.md").write_text(
    "---\ntitle: Deferred twice\nstatus: deferred\ncreated: 2026-01-01\n---\n\n## Decision\nIoseb, 2026-01-02: "
    f"deferred.\nIoseb, {time.strftime('%Y-%m-%d')}: deferred again.\n")
b = script("handoffs.py", "", "brief")
check("undated deferral falls back to the created date", "Undated deferral" in b)
check("the latest deferral date counts", "Deferred twice" not in b)
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
