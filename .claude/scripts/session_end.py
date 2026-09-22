#!/usr/bin/env python3
"""SessionEnd hook (ADR 0010).

SessionEnd hooks get about 1.5 seconds, so this only starts the summarizer as a
detached background process and returns immediately.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import GUARD_ENV, ROOT, STATE, read_hook_input  # noqa: E402


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        return
    STATE.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, **{GUARD_ENV: "1", "CLAUDE_PROJECT_DIR": str(ROOT)})
    with open(STATE / "summarizer.log", "a") as log:
        subprocess.Popen(
            [sys.executable, str(ROOT / ".claude" / "scripts" / "summarize_session.py"),
             transcript, data.get("session_id", "unknown"), data.get("reason", "other")],
            stdout=log, stderr=log, stdin=subprocess.DEVNULL, env=env, start_new_session=True,
        )


if __name__ == "__main__":
    main()
