#!/usr/bin/env python3
"""Task handoffs (ADR 0022). Used by the resume, handoff and parallel-task skills.

  handoffs.py path <task>   absolute path of a task's handoff (always in the main folder,
                            also when called from a worktree)
  handoffs.py list          open tasks, newest first
  handoffs.py brief         everything the resume skill shows: open tasks, phase status,
                            last session's next steps, proposals, failed summaries
  handoffs.py index         rebuild memory/working/handoffs/_index.md
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (HANDOFFS, ROOT, SESSIONS, frontmatter, list_handoffs, open_proposals,  # noqa: E402
                    summary_failures, task_slug, write_handoff_index)


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


def last_summary():
    files = sorted(SESSIONS.glob("*.md"), key=lambda f: (frontmatter(f)[0].get("ended", ""), f.name))
    if not files:
        return ""
    meta, body = frontmatter(files[-1])
    unreviewed = sum(frontmatter(f)[0].get("reviewed", "no") == "no" for f in files)
    m = re.search(r"## Next steps\n(.*?)(\n## |\Z)", body, re.S)
    nxt = m.group(1).strip() if m else ""
    flag = " (unreviewed: skim it and correct anything wrong)" if meta.get("reviewed", "no") == "no" else ""
    older = (f"\n{unreviewed - 1} older summaries are also unreviewed: ask Ioseb whether to check them now."
             if unreviewed > 1 else "")
    return (f"Last session summary: {files[-1].name}{flag}\n{meta.get('title', '')}\nNext steps it recorded:\n"
            f"{nxt[:1200]}" + older)


def failures_text():
    fails = summary_failures()
    if not fails:
        return ""
    lines = [f"- session {sid[:8]} at {v.get('time', '?')}: {v.get('error', '')[:160]}\n  redo: python3 "
             f".claude/scripts/summarize_session.py {v.get('transcript', '?')} {sid} retry" for sid, v in fails.items()]
    return ("SESSION SUMMARY FAILED (tell Ioseb in one sentence and offer to redo it; "
            "'Not logged in' means he must run claude and /login first):\n" + "\n".join(lines))


def tasks_text():
    tasks = list_handoffs()
    if not tasks:
        return "Open tasks: none."
    lines = [f"{i}. {slug} [{m.get('type', '?')}] branch {m.get('branch', '?')}, updated {m['updated']}"
             + (f", worktree {m['worktree']}" if m.get("worktree") else "") for i, (slug, m) in enumerate(tasks, 1)]
    return "Open tasks (memory/working/handoffs/):\n" + "\n".join(lines)


def brief():
    parts = [tasks_text(), phase_status(), last_summary(), failures_text()]
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
        write_handoff_index()
    else:
        print(brief())


if __name__ == "__main__":
    main()
