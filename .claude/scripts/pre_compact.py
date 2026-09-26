#!/usr/bin/env python3
"""PreCompact hook (ADR 0012).

Saves a mechanical snapshot (git status, recent user requests) per session in
memory/working/snapshots/, in case Claude did not get to write one. It prints nothing: Claude Code
does not accept extra context from a PreCompact hook (a real compaction test on
2026-09-26 showed it rejected), so what must survive the compaction is in the
"Compact instructions" section of CLAUDE.md, and the SessionStart(compact) hook
reinjects the session's task handoff or this snapshot afterwards.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from common import GUARD_ENV, ROOT, SNAPSHOTS, is_real_user_text, read_hook_input, scrub, session_state_path  # noqa: E402


def recent_user_messages(transcript_path, limit=6):
    msgs = []
    try:
        with open(transcript_path, errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("type") != "user" or e.get("isMeta"):
                    continue
                c = (e.get("message") or {}).get("content")
                if is_real_user_text(c):
                    msgs.append(c.strip().replace("\n", " ")[:300])
    except Exception:
        pass
    return msgs[-limit:]


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    try:
        git = subprocess.run(["git", "-C", str(ROOT), "status", "--short"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        git = "(git unavailable)"
    snap = [
        f"# Auto snapshot before compaction ({time.strftime('%Y-%m-%d %H:%M')}, trigger: {data.get('trigger', '?')})",
        "",
        "Written by a hook, not by Claude. The task handoff comes first; this is the fallback.",
        "",
        "## Uncommitted changes",
        "```", git.rstrip() or "(clean)", "```",
        "",
        "## Last user requests",
    ] + [f"- {m}" for m in recent_user_messages(data.get("transcript_path", ""))]
    # one file per session: parallel terminals never overwrite each other's snapshot
    (SNAPSHOTS / session_state_path(data.get("session_id")).with_suffix(".md").name).write_text(scrub("\n".join(snap)) + "\n")


if __name__ == "__main__":
    main()
