#!/usr/bin/env python3
"""PreToolUse hook: the harness guard (foundation v2 step 3, ADR 0024).

Runs before every tool use and refuses what must never happen automatically, including
things the permission lists in settings.json cannot express:
  - writing files outside the project, its worktrees, the scratchpad or Claude's own memory
  - reading or touching .env, secrets/ or credential files through any tool, including the shell
    and search patterns (the Read deny rules do not cover "cat .env")
  - committing on master, pushing to master (named, HEAD, or a bare push while on master),
    force pushing, merging a pull request
  - deleting or editing visitor data (the project's data/, logs/, leads.csv)
Commit messages and pull request texts may mention those files: only the text after -m,
--title or --body is exempt, never the command itself.
Allowed actions pass through silently to the normal permission lists.
"""
import json
import os
import re
import shlex
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
# the text of a commit message or pull request, which may mention secret file names harmlessly
MESSAGE = re.compile(r"(?:-m|--message|--title|--body)\s+(\"\$\(cat <<'?(\w+)'?.*?\n\2\s*\)\"|\"(?:[^\"\\]|\\.)*\"|'[^']*')",
                     re.S)
DELETE = {"rm", "unlink", "shred", "truncate", "rmdir"}
PROTECTED_BRANCHES = {"master", "main"}


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


def is_visitor_data(path, cwd):
    p = Path(path).expanduser()
    p = (Path(cwd) / p) if not p.is_absolute() else p
    for root in (ROOT, MAIN_ROOT):
        if inside(p, [root]):
            rel = str(p.resolve().relative_to(root.resolve()))
            if re.match(r"(data|logs)(/|$)|leads\.csv$", rel):
                return True
    return False


def segments(cmd):
    """The simple commands in a shell line, split at && || ; | and newlines."""
    return [s.strip() for s in re.split(r"&&|\|\||[;|\n]", cmd) if s.strip()]


def words(segment):
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def check_push(args, cwd):
    """args: the words after 'push'."""
    if any(a in ("-f", "--force", "--mirror") or a.startswith("--force") for a in args):
        deny("no force push. Push the branch normally and open a pull request.")
    refs = [a for a in args if not a.startswith("-")][1:]  # the first is the remote
    for r in refs:
        if r.startswith("+"):
            deny("no force push (a + refspec). Push the branch normally and open a pull request.")
        dst = r.split(":")[-1].removeprefix("refs/heads/")
        if dst in PROTECTED_BRANCHES:
            deny("no push to master. Push the branch and open a pull request.")
    if (not refs or any(r.split(":")[-1] == "HEAD" for r in refs)) and current_branch(cwd) in PROTECTED_BRANCHES:
        deny("this push would update master (you are on master). Create a branch first.")


def check_bash(cmd, cwd):
    if SECRET.search(MESSAGE.sub(" ", cmd)):
        deny("shell commands may not touch .env, secrets/ or credential files. Ask Ioseb to do it himself.")
    if re.search(r"\bgit\s+(clean|reset\s+--hard)\b", cmd):
        deny("git clean and hard reset destroy uncommitted work.")
    for seg in segments(MESSAGE.sub(" ", cmd)):
        w = words(seg)
        if not w:
            continue
        if w[0] == "sudo":
            w = w[1:]
        if w[:3] == ["gh", "pr", "merge"]:
            deny("merging is Ioseb's approval step. He merges on GitHub.")
        if w and w[0] == "git":
            sub = next((i for i, a in enumerate(w[1:], 1) if not a.startswith("-") and w[i - 1] not in ("-C", "-c")), None)
            if sub is not None and w[sub] == "push":
                check_push(w[sub + 1:], cwd)
            if sub is not None and w[sub] == "commit" and current_branch(cwd) in PROTECTED_BRANCHES:
                deny("no commits on master. Create a branch first (git checkout -b maintain-... or phase-N-...).")
        if w and w[0] in DELETE and any(is_visitor_data(a, cwd) for a in w[1:] if not a.startswith("-")):
            deny("visitor data (data/, logs/, leads.csv) is never deleted by Claude.")


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    cwd = data.get("cwd") or str(ROOT)

    if tool == "Bash":
        check_bash(inp.get("command", ""), cwd)
        return
    targets = [str(inp.get(k)) for k in ("file_path", "notebook_path", "path", "glob") if inp.get(k)]
    if tool == "Glob" and inp.get("pattern"):
        targets.append(str(inp["pattern"]))
    if any(SECRET.search(t) for t in targets):
        deny(".env, secrets/ and credential files are never read, searched or changed by Claude.")
    path = inp.get("file_path") or inp.get("notebook_path") or ""
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit") and path:
        if not inside(path, WRITABLE):
            deny(f"{path} is outside the project, its worktrees and the scratchpad.")
        if is_visitor_data(path, cwd):
            deny("visitor data (data/, logs/, leads.csv) is never edited by Claude.")


if __name__ == "__main__":
    main()
