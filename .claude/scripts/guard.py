#!/usr/bin/env python3
"""PreToolUse hook: the harness guard (foundation v2 step 3, ADR 0024).

Runs before every tool use and refuses what must never happen automatically, including
things the permission lists in settings.json cannot express:
  - writing files outside the project, its worktrees, the scratchpad or Claude's own memory
  - reading or touching .env, secrets/ or credential files through any tool, including the shell
    (the Read deny rules do not cover "cat .env")
  - committing on master, pushing to master, merging a pull request
  - deleting visitor data (data/, logs/, leads.csv)
Allowed actions pass through silently to the normal permission lists.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import GUARD_ENV, MAIN_ROOT, ROOT, current_branch, read_hook_input  # noqa: E402

HOME = Path.home()
WRITABLE = [ROOT, MAIN_ROOT, MAIN_ROOT.parent / f"{MAIN_ROOT.name}-wt",
            HOME / ".claude" / "projects",            # Claude's own auto memory
            Path("/private/tmp"), Path("/tmp")]       # scratchpad and temporary test folders
SECRET = re.compile(r"(?<![\w.])secrets/|(?<![\w.])secrets$|"
                    r"(?<![\w.])(\.env(?!\.example)(\.[\w]+)?|client_secret[\w.]*json|google-token[\w.]*json|"
                    r"[\w-]*credentials[\w-]*\.json|[\w-]*service-account[\w-]*\.json)(?![\w])")
VISITOR_DATA = re.compile(r"(?<![\w])(data/|logs/|leads\.csv)")


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": f"Harness guard (ADR 0024): {reason}"}}))
    sys.exit(0)


def inside(path, roots):
    try:
        p = Path(path).expanduser().resolve()
    except Exception:
        return False
    return any(p == r.resolve() or r.resolve() in p.parents for r in roots)


def check_bash(cmd, cwd):
    if SECRET.search(cmd):
        deny("shell commands may not touch .env, secrets/ or credential files. Ask Ioseb to do it himself.")
    if re.search(r"\bgh\s+pr\s+merge\b", cmd):
        deny("merging is Ioseb's approval step. He merges on GitHub.")
    push = re.search(r"\bgit\b[^|;&]*\bpush\b[^|;&]*", cmd)
    if push and re.search(r"\b(master|main)\b|--force|\s-f\b", push.group(0)):
        deny("no push to master and no force push. Push the branch and open a pull request.")
    if re.search(r"\bgit\b[^|;&]*\bcommit\b", cmd) and current_branch(cwd) in ("master", "main"):
        deny("no commits on master. Create a branch first (git checkout -b maintain-... or phase-N-...).")
    if re.search(r"\b(rm|unlink|shred|truncate)\b", cmd) and VISITOR_DATA.search(cmd):
        deny("visitor data (data/, logs/, leads.csv) is never deleted by Claude.")
    if re.search(r"\bgit\s+(clean|reset\s+--hard)\b", cmd):
        deny("git clean and hard reset destroy uncommitted work.")


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    cwd = data.get("cwd") or str(ROOT)

    if tool == "Bash":
        check_bash(inp.get("command", ""), cwd)
        return
    path = inp.get("file_path") or inp.get("notebook_path") or inp.get("path") or ""
    if path and SECRET.search(str(path)):
        deny(".env, secrets/ and credential files are never read or changed by Claude.")
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit") and path:
        if not inside(path, WRITABLE):
            deny(f"{path} is outside the project, its worktrees and the scratchpad.")
        for root in (ROOT, MAIN_ROOT):
            if inside(path, [root]) and re.match(r"(data|logs)/|leads\.csv$", str(Path(path).resolve().relative_to(root.resolve()))):
                deny("visitor data (data/, logs/, leads.csv) is never edited by Claude.")


if __name__ == "__main__":
    main()
