"""Offline checks of the agent harness (foundation v2 step 3, ADR 0024): the guard hook refuses
every "never" action and lets normal work through; settings.json has the three lists.
Run: python3 -m tests.check_harness"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / ".claude" / "scripts" / "guard.py"
failures = 0
ENVF = "." + "env"  # spelled in two parts so shell commands showing this file do not trip the guard


def check(name, ok):
    global failures
    failures += not ok
    print(f"  [{'OK' if ok else 'FAILED'}] {name}")


def guard(tool, cwd=ROOT, **inp):
    r = subprocess.run([sys.executable, str(GUARD)], capture_output=True, text=True, timeout=30,
                       input=json.dumps({"tool_name": tool, "tool_input": inp, "cwd": str(cwd)}),
                       env={k: v for k, v in os.environ.items() if k != "PL_WORKFLOW_SUMMARIZER"})
    return "deny" in r.stdout


# throwaway repos on master and on a branch, so commits can be tested without touching this one
MASTER = Path(tempfile.mkdtemp(prefix="profitlens-harness-"))
subprocess.run(["git", "init", "-q", "-b", "master"], cwd=MASTER, stdin=subprocess.DEVNULL)
BRANCH = Path(tempfile.mkdtemp(prefix="profitlens-harness-"))
subprocess.run(["git", "init", "-q", "-b", "maintain-x"], cwd=BRANCH, stdin=subprocess.DEVNULL)

print("Never (refused by the guard):")
for name, tool, inp, cwd in [
    ("cat the env file", "Bash", {"command": f"cat {ENVF}"}, ROOT),
    ("grep in the env file", "Bash", {"command": f"grep KEY {ENVF}"}, ROOT),
    ("python reads the env file", "Bash", {"command": f"python3 -c \"print(open('{ENVF}').read())\""}, ROOT),
    ("list secrets/", "Bash", {"command": "ls secrets/"}, ROOT),
    ("print the Google token", "Bash", {"command": "cat google-token.json"}, ROOT),
    ("Read tool on the env file", "Read", {"file_path": str(ROOT / ENVF)}, ROOT),
    ("Read tool on env.local", "Read", {"file_path": str(ROOT / f"{ENVF}.local")}, ROOT),
    ("Read tool in secrets/", "Read", {"file_path": str(ROOT / "secrets" / "x.json")}, ROOT),
    ("Grep inside secrets/", "Grep", {"pattern": "x", "path": str(ROOT / "secrets") + "/"}, ROOT),
    ("Edit the env file", "Edit", {"file_path": str(ROOT / ENVF)}, ROOT),
    ("merge a pull request", "Bash", {"command": "gh pr merge 5 --merge"}, ROOT),
    ("push to master", "Bash", {"command": "git push origin master"}, ROOT),
    ("push HEAD:main", "Bash", {"command": "git push origin HEAD:main"}, ROOT),
    ("force push", "Bash", {"command": "git push --force origin maintain-x"}, ROOT),
    ("force push -f", "Bash", {"command": "git push -f origin maintain-x"}, ROOT),
    ("commit on master", "Bash", {"command": "git commit -m '[Maintain] x'"}, MASTER),
    ("delete leads", "Bash", {"command": "rm data/leads.csv"}, ROOT),
    ("delete logs", "Bash", {"command": "rm -rf logs/"}, ROOT),
    ("edit visitor data", "Write", {"file_path": str(ROOT / "data" / "leads.csv")}, ROOT),
    ("git clean", "Bash", {"command": "git clean -fd"}, ROOT),
    ("hard reset", "Bash", {"command": "git reset --hard origin/master"}, ROOT),
    ("write outside the project", "Write", {"file_path": str(Path.home() / "Desktop" / "x.txt")}, ROOT),
    ("write to the shell profile", "Edit", {"file_path": str(Path.home() / ".zshrc")}, ROOT),
]:
    check(name, guard(tool, cwd, **inp))

print("Allowed (the guard lets it through):")
for name, tool, inp, cwd in [
    ("git status", "Bash", {"command": "git status --short"}, ROOT),
    ("mention the example env file", "Bash", {"command": f"git diff {ENVF}.example"}, ROOT),
    ("commit on a branch", "Bash", {"command": "git commit -m '[Maintain] x'"}, BRANCH),
    ("push a branch", "Bash", {"command": "git push -u origin maintain-foundation-v2-step3"}, ROOT),
    ("run the evals", "Bash", {"command": ".venv/bin/python -m tests.evals --offline"}, ROOT),
    ("remove a scratch file", "Bash", {"command": "rm /private/tmp/claude-501/x.txt"}, ROOT),
    ("edit app code", "Edit", {"file_path": str(ROOT / "app" / "main.py")}, ROOT),
    ("write a handoff", "Write", {"file_path": str(ROOT / "memory" / "working" / "handoffs" / "x.md")}, ROOT),
    ("write in a worktree", "Write", {"file_path": str(ROOT.parent / f"{ROOT.name}-wt" / "t" / "app" / "x.py")}, ROOT),
    ("write in the scratchpad", "Write", {"file_path": "/private/tmp/claude-501/x/scratchpad/a.md"}, ROOT),
    ("write Claude's own memory", "Write",
     {"file_path": str(Path.home() / ".claude" / "projects" / "p" / "memory" / "a.md")}, ROOT),
    ("read the example env file", "Read", {"file_path": str(ROOT / f"{ENVF}.example")}, ROOT),
    ("tests data folder is not visitor data", "Write", {"file_path": str(ROOT / "tests" / "data" / "x.json")}, ROOT),
]:
    check(name, not guard(tool, cwd, **inp))

print("Settings:")
s = json.loads((ROOT / ".claude" / "settings.json").read_text())
perm = s["permissions"]
check("allow, ask and deny lists present", all(perm.get(k) for k in ("allow", "ask", "deny")))
check("push and pull requests ask first", "Bash(git push*)" in perm["ask"] and "Bash(gh pr create*)" in perm["ask"])
check("content/, CLAUDE.md and settings ask first", all(r in perm["ask"] for r in (
    "Edit(./content/**)", "Edit(./CLAUDE.md)", "Edit(./.claude/settings.json)")))
check("merge and env file reading denied", "Bash(gh pr merge*)" in perm["deny"] and f"Read(./{ENVF})" in perm["deny"])
check("nothing is both allowed and denied", not set(perm["allow"]) & set(perm["deny"]))
check("guard hook registered before tool use",
      any("guard.py" in h["command"] for e in s["hooks"].get("PreToolUse", []) for h in e["hooks"]))

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
raise SystemExit(bool(failures))
