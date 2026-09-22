#!/usr/bin/env python3
"""PostToolUse hook for Write/Edit: authoring guardrail for chatbot-facing text.

Checks files the chatbot reads or shows to visitors:
  content/*.md, app/prompts/*, app/static/*, app/**/*.html|js|css
R4: no em dash or en dash.  R2: no percentages in content/.
On a hit, feeds the problem back to Claude (decision: block) so it fixes it.
Runtime guardrails in the chat service (spec G1 to G3) are separate and still required.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import GUARD_ENV, ROOT, read_hook_input  # noqa: E402

DASHES = re.compile("[–—]")
PERCENT = re.compile(r"\d\s?%|\bpercent\b", re.I)


def in_scope(rel):
    if rel.startswith("content/") and rel.endswith(".md"):
        return True
    if rel.startswith(("app/prompts/", "app/static/")):
        return True
    return rel.startswith("app/") and rel.endswith((".html", ".js", ".css"))


def check(path):
    rel = os.path.relpath(path, ROOT)
    problems = []
    for i, line in enumerate(open(path, errors="replace"), 1):
        if DASHES.search(line):
            problems.append(f"{rel}:{i} has an em or en dash (rule R4): {line.strip()[:100]}")
        if rel.startswith("content/") and PERCENT.search(line):
            problems.append(f"{rel}:{i} has a percentage (rule R2): {line.strip()[:100]}")
    return problems


def main():
    if "--all" in sys.argv:  # manual check of every in-scope file, used by the phase-gate skill
        problems = []
        for p in sorted(list(ROOT.glob("content/**/*")) + list(ROOT.glob("app/**/*"))):
            if p.is_file() and in_scope(str(p.relative_to(ROOT))):
                problems += check(p)
        print("\n".join(problems) or "OK: no dashes or percentages in chatbot text")
        sys.exit(1 if problems else 0)
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    path = (data.get("tool_input") or {}).get("file_path", "")
    try:
        rel = os.path.relpath(path, ROOT)
    except ValueError:
        return
    if not in_scope(rel) or not os.path.exists(path):
        return
    problems = check(path)
    if problems:
        print(json.dumps({"decision": "block", "reason": "Chatbot text guardrail:\n" + "\n".join(problems[:15])
                          + "\nFix these lines (commas, periods or parentheses instead of dashes; remove figures)."}))


if __name__ == "__main__":
    main()
