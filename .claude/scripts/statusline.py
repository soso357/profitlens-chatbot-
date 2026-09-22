#!/usr/bin/env python3
"""Project statusline (ADR 0012).

Shows: model | folder (branch) | context bar and % | compactions | open proposals.
Also records the context % per session so the context_guard hook can act on it,
because hooks do not receive the context percentage themselves.
"""
import json
import subprocess
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import COMPACT_PCT, HANDOFF_PCT, MAX_COMPACTIONS, load_state, open_proposals, save_state  # noqa: E402

DIM, RED, YEL, GRN, CYA, BOLD, RST = "\033[2m", "\033[31m", "\033[33m", "\033[32m", "\033[36m", "\033[1m", "\033[0m"


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        d = {}
    model = (d.get("model") or {}).get("display_name") or "Claude"
    cwd = (d.get("workspace") or {}).get("current_dir") or d.get("cwd") or "."
    sid = d.get("session_id") or "unknown"
    pct = (d.get("context_window") or {}).get("used_percentage")

    branch = ""
    try:
        branch = subprocess.run(["git", "--no-optional-locks", "-C", cwd, "branch", "--show-current"],
                                capture_output=True, text=True, timeout=1).stdout.strip()
    except Exception:
        pass

    state = load_state(sid)
    if pct is not None:
        state["pct"] = float(pct)
        try:
            save_state(sid, state)
        except Exception:
            pass
    n = int(state.get("compactions", 0))

    parts = [f"{CYA}{model}{RST}", f"{DIM}{cwd.rsplit('/', 1)[-1]}{RST}" + (f" {YEL}({branch}){RST}" if branch else "")]

    if pct is not None:
        p = int(pct)
        filled = min(10, p // 10)
        bar = "#" * filled + "." * (10 - filled)
        if p >= COMPACT_PCT:
            parts.append(f"{RED}[{bar}] {p}% compacting{RST}")
        elif p >= HANDOFF_PCT:
            parts.append(f"{YEL}[{bar}] {p}% handoff{RST}")
        else:
            parts.append(f"{GRN}[{bar}] {p}%{RST}")

    if n >= MAX_COMPACTIONS:
        parts.append(f"{BOLD}{RED}STOP: {n} compactions. Open a new terminal or /clear{RST}")
    elif n > 0:
        parts.append(f"{YEL}compactions {n}/{MAX_COMPACTIONS}{RST}")

    try:
        props = [p for p in open_proposals() if p[1] == "proposed"]
        if props:
            parts.append(f"{CYA}{len(props)} proposal{'s' if len(props) > 1 else ''} to review{RST}")
    except Exception:
        pass

    print(" | ".join(parts))


if __name__ == "__main__":
    main()
