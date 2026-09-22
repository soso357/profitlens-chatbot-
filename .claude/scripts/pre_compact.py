#!/usr/bin/env python3
"""PreCompact hook (ADR 0012).

1. Saves a mechanical snapshot (git status, recent user requests) next to the
   handoff, in case Claude did not get to write one.
2. Gives the compactor instructions about what must survive.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from common import GUARD_ENV, HANDOFF, ROOT, WORKING, emit_context, is_real_user_text, read_hook_input, scrub  # noqa: E402


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
    WORKING.mkdir(parents=True, exist_ok=True)
    try:
        git = subprocess.run(["git", "-C", str(ROOT), "status", "--short"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        git = "(git unavailable)"
    handoff_age = time.time() - HANDOFF.stat().st_mtime if HANDOFF.exists() else None
    snap = [
        f"# Auto snapshot before compaction ({time.strftime('%Y-%m-%d %H:%M')}, trigger: {data.get('trigger', '?')})",
        "",
        "Written by a hook, not by Claude. Use handoff.md first; this is the fallback.",
        "",
        "## Uncommitted changes",
        "```", git.rstrip() or "(clean)", "```",
        "",
        "## Last user requests",
    ] + [f"- {m}" for m in recent_user_messages(data.get("transcript_path", ""))]
    (WORKING / "snapshot.md").write_text(scrub("\n".join(snap)) + "\n")

    fresh = handoff_age is not None and handoff_age < 3600
    emit_context("PreCompact", (
        "Compaction instructions for the ProfitLens project: keep the current phase and its gate status, "
        "every decision the user made in this session and which option they chose, questions still waiting "
        "for the user, files changed, and the exact next step. Drop tool output, file dumps and research detail "
        "that is already saved in docs/. "
        + ("memory/working/handoff.md was updated in the last hour and is authoritative." if fresh
           else "No fresh handoff exists; memory/working/snapshot.md has a mechanical snapshot.")
    ))


if __name__ == "__main__":
    main()
