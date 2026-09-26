#!/usr/bin/env python3
"""PostToolUse hook for Write and Edit (ADR 0022).

When Claude writes a task handoff (memory/working/handoffs/<task>.md), remember that this
session owns that task, so after a compaction the SessionStart hook reinjects this
terminal's own handoff and never another terminal's. Also rebuilds the task index.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import GUARD_ENV, HANDOFFS, load_state, read_hook_input, save_state, write_handoff_index  # noqa: E402


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
    sid = data.get("session_id") or "unknown"
    state = load_state(sid)
    state["task"] = p.stem
    save_state(sid, state)
    write_handoff_index()


if __name__ == "__main__":
    main()
