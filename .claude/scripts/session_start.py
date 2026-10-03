#!/usr/bin/env python3
"""SessionStart hook (ADR 0009, 0022).

startup / resume / clear: load nothing (Ioseb's choice, ADR 0022). One line says how to
continue. Tidies the handoff index.
compact: count the compaction, reinject this session's own task handoff (or its
snapshot), and ask for a new terminal.
The full brief (open tasks, phase status, proposals) is shown by the
resume skill through handoffs.py brief.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (GUARD_ENV, MAX_COMPACTIONS, ROOT, SNAPSHOTS, emit_context, handoff_for_session,  # noqa: E402
                    list_handoffs, load_state, read_hook_input, save_state, session_state_path)


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    source = data.get("source", "startup")
    sid = data.get("session_id") or "unknown"
    cwd = data.get("cwd") or str(ROOT)

    if source == "compact":
        state = load_state(sid)
        state["compactions"] = int(state.get("compactions", 0)) + 1
        save_state(sid, state)
        out = [f"This session was just compacted (compaction {state['compactions']})."]
        own = handoff_for_session(state, cwd)
        snap = SNAPSHOTS / session_state_path(sid).with_suffix(".md").name
        for f in (own, snap):
            if f and f.exists():
                out.append(f"--- {f.name} (this session's task) ---\n{f.read_text()[:4000]}")
                break
        if state["compactions"] >= MAX_COMPACTIONS:
            out.append("Compaction is only a safety net (ADR 0022). Finish the current small step, update this "
                       "task's handoff (skill: handoff), commit, then tell Ioseb once: open a new terminal in "
                       "this folder, start claude and say resume.")
        emit_context("SessionStart", "\n\n".join(out))
        return

    try:
        subprocess.Popen([sys.executable, str(ROOT / ".claude" / "scripts" / "handoffs.py"), "index"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        pass

    n = len(list_handoffs())
    emit_context("SessionStart", f"ProfitLens: nothing loaded yet (ADR 0022). {n} open task{'s' if n != 1 else ''}. "
                 "Do not start on any of them by yourself. When Ioseb says resume, use the resume skill.")


if __name__ == "__main__":
    main()
