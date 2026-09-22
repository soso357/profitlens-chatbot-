#!/usr/bin/env python3
"""UserPromptSubmit hook (ADR 0012).

Reads the context % recorded by the statusline. Once per compaction cycle, at
HANDOFF_PCT or more, tells Claude to write the handoff before answering. Once
per session, after MAX_COMPACTIONS, tells Claude to recommend a fresh session.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import GUARD_ENV, HANDOFF_PCT, MAX_COMPACTIONS, emit_context, load_state, read_hook_input, save_state  # noqa: E402


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    sid = data.get("session_id") or "unknown"
    state = load_state(sid)
    pct = float(state.get("pct") or 0)
    cycle = int(state.get("compactions", 0))
    notes = []

    if pct >= HANDOFF_PCT and state.get("handoff_nudged_cycle", -1) != cycle:
        notes.append(
            f"CONTEXT {int(pct)}%: before answering, run the handoff skill: update memory/working/handoff.md "
            "with the current goal, decisions made, files touched, open questions and the exact next step. "
            "Keep it under 60 lines. Then answer the user normally. Auto compaction happens at 70%."
        )
        state["handoff_nudged_cycle"] = cycle

    if cycle >= MAX_COMPACTIONS and not state.get("limit_nudged"):
        notes.append(
            f"SESSION LIMIT: this session has been compacted {cycle} times. At the end of this reply, tell the user "
            "plainly that it is time to continue in a new terminal window (the handoff and session summary carry "
            "the context over) or to type /clear. Say it once."
        )
        state["limit_nudged"] = True

    if notes:
        save_state(sid, state)
        emit_context("UserPromptSubmit", "\n\n".join(notes))


if __name__ == "__main__":
    main()
