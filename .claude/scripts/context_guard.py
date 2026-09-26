#!/usr/bin/env python3
"""UserPromptSubmit hook (ADR 0022).

Reads the context % recorded by the statusline (hooks do not receive it themselves).
Once per compaction cycle each:
  HANDOFF_PCT (60): update this task's handoff before answering.
  STOP_PCT (70): soft stop (ADR 0023 C3): finish the step, hand off, commit, ask for a new terminal.
Once per session after MAX_COMPACTIONS: recommend a new terminal.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (GUARD_ENV, HANDOFF_PCT, MAX_COMPACTIONS, STOP_PCT, emit_context, load_state,  # noqa: E402
                    read_hook_input, save_state)


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    sid = data.get("session_id") or "unknown"
    state = load_state(sid)
    pct = float(state.get("pct") or 0)
    cycle = int(state.get("compactions", 0))
    notes = []

    if pct >= STOP_PCT and state.get("stop_nudged_cycle", -1) != cycle:
        notes.append(
            f"CONTEXT {int(pct)}%, time for a new session (ADR 0022). Do not start new work. Finish only the current "
            "small step, update this task's handoff (skill: handoff), commit on the branch, then tell Ioseb in two "
            "lines: open a new terminal in this folder, start claude, say resume. If Ioseb insists on continuing "
            "here, continue (the stop is soft); compaction happens by itself at 85%."
        )
        state["stop_nudged_cycle"] = cycle
        state["handoff_nudged_cycle"] = cycle
    elif pct >= HANDOFF_PCT and state.get("handoff_nudged_cycle", -1) != cycle:
        notes.append(
            f"CONTEXT {int(pct)}%: before answering, update this task's handoff (skill: handoff) with the fixed "
            "template: goal, state, decisions, open questions, next step, do not redo, files. Then answer normally. "
            "At 70% the session should end."
        )
        state["handoff_nudged_cycle"] = cycle

    if cycle >= MAX_COMPACTIONS and not state.get("limit_nudged"):
        notes.append(
            "SESSION WAS COMPACTED: at the end of this reply, tell Ioseb once that it is time to continue in a new "
            "terminal (start claude there and say resume). The task handoff carries the context."
        )
        state["limit_nudged"] = True

    if notes:
        save_state(sid, state)
        emit_context("UserPromptSubmit", "\n\n".join(notes))


if __name__ == "__main__":
    main()
