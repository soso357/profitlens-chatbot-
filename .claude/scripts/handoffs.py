#!/usr/bin/env python3
"""Task handoffs (ADR 0022). Used by the resume, handoff and parallel-task skills.

  handoffs.py path <task>   absolute path of a task's handoff (always in the main folder,
                            also when called from a worktree)
  handoffs.py list          open tasks, newest first
  handoffs.py brief         everything the resume skill shows: open tasks, phase status, proposals
  handoffs.py index         delete handoffs done more than 14 days ago, rebuild _index.md
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (HANDOFFS, ROOT, cleanup_done_handoffs, deferred_due, list_handoffs, open_proposals,  # noqa: E402
                    stale_semantic, task_slug, write_handoff_index)


def phase_status():
    for name in ("progress.md", "plan.md"):
        try:
            text = (ROOT / "docs" / name).read_text()
        except Exception:
            continue
        rows = [l for l in text.splitlines() if l.startswith("| ") and ("IN PROGRESS" in l or "WAITING" in l)]
        if rows:
            return f"Phase status (docs/{name}):\n" + "\n".join(rows[:4])
    return ""


def tasks_text():
    tasks = list_handoffs()
    if not tasks:
        return "Open tasks: none."
    lines = [f"{i}. {slug} [{m.get('type', '?')}] branch {m.get('branch', '?')}, updated {m['updated']}"
             + (f", worktree {m['worktree']}" if m.get("worktree") else "") for i, (slug, m) in enumerate(tasks, 1)]
    return "Open tasks (memory/working/handoffs/):\n" + "\n".join(lines)


def staleness_text():
    out = []
    stale = stale_semantic()
    if stale:
        out.append("Memory to re-check with Ioseb, then set last_verified to today: "
                   + "; ".join(f"{p.name} ({n})" for p, n in stale))
    due = deferred_due()
    if due:
        out.append("Deferred proposals due to be asked again: "
                   + "; ".join(f"{name[:4]} {title[:60]} ({age} days)" for name, title, age in due))
    return "\n".join(out)


def brief():
    parts = [tasks_text(), phase_status(), staleness_text()]
    props = open_proposals()
    if props:
        lines = [f"- {name[:4]} [{status}] {title[:90]}" for name, status, title in props]
        extra = (" More than 8 are waiting: suggest a short review session."
                 if sum(s == "proposed" for _, s, _ in props) > 8 else "")
        parts.append("Open improvement proposals (mention the 'proposed' ones once, at a natural pause)."
                     + extra + "\n" + "\n".join(lines))
    return "\n\n".join(p for p in parts if p)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "brief"
    if cmd == "path":
        print(HANDOFFS / f"{task_slug(' '.join(sys.argv[2:]))}.md")
    elif cmd == "list":
        print(tasks_text())
    elif cmd == "index":
        cleanup_done_handoffs()
        write_handoff_index()
    else:
        print(brief())


if __name__ == "__main__":
    main()
