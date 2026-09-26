#!/usr/bin/env python3
"""PostToolUse hook for Write and Edit (ADR 0022).

When Claude writes an open task handoff on its own branch (memory/working/handoffs/<task>.md),
remember that this session owns that task, so after a compaction the SessionStart hook reinjects this
terminal's own handoff and never another terminal's. Also rebuilds the task index.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import (GUARD_ENV, HANDOFFS, ROOT, current_branch, frontmatter, load_state, read_hook_input,  # noqa: E402
                    save_state, write_handoff_index)


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    path = (data.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".md"):
        return
    p = Path(path)
    try:
        if p.resolve().parent != HANDOFFS.resolve() or p.name.startswith("_"):
            return
    except Exception:
        return
    write_handoff_index()
    # Claim the task only if it is open and on this session's own branch: writing another
    # terminal's first handoff (skill: parallel-task) or closing an old task must not claim it.
    try:
        meta, _ = frontmatter(p)
    except Exception:
        return
    branch = current_branch(data.get("cwd") or ROOT)
    if meta.get("status", "open") == "done" or (meta.get("branch") and meta.get("branch") != branch):
        return
    sid = data.get("session_id") or "unknown"
    state = load_state(sid)
    state["task"] = p.stem
    save_state(sid, state)


if __name__ == "__main__":
    main()
