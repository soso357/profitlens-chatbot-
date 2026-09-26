#!/usr/bin/env python3
"""SessionStart hook (ADR 0009, 0012).

startup / resume / clear: brief Claude with the plan status, the last session's
next steps, open improvement proposals and any leftover handoff. Rebuild the
memory index.
compact: count the compaction, reinject the handoff, warn at the limit.
Output stays short: this text costs context in every session.
"""
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from common import (GUARD_ENV, HANDOFF, MAX_COMPACTIONS, ROOT, SESSIONS, WORKING, emit_context,  # noqa: E402
                    frontmatter, load_state, open_proposals, read_hook_input, save_state, summary_failures)


def plan_status():
    try:
        text = (ROOT / "docs" / "plan.md").read_text()
        rows = [l for l in text.splitlines() if l.startswith("| ") and ("IN PROGRESS" in l or "WAITING" in l)]
        return "\n".join(rows[:4])
    except Exception:
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
    return (f"Last session: {files[-1].name}{flag}\n{meta.get('title', '')}\nNext steps it recorded:\n{nxt[:1200]}"
            + older)


def main():
    if os.environ.get(GUARD_ENV):
        return
    data = read_hook_input()
    source = data.get("source", "startup")
    sid = data.get("session_id") or "unknown"
    out = []

    if source == "compact":
        state = load_state(sid)
        state["compactions"] = int(state.get("compactions", 0)) + 1
        save_state(sid, state)
        n = state["compactions"]
        out.append(f"This session was just compacted (compaction {n} of {MAX_COMPACTIONS} recommended).")
        for f in (HANDOFF, WORKING / "snapshot.md"):
            if f.exists() and time.time() - f.stat().st_mtime < 3 * 3600:
                out.append(f"--- {f.relative_to(ROOT)} ---\n{f.read_text()[:4000]}")
                break
        if n >= MAX_COMPACTIONS:
            out.append("LIMIT REACHED: tell the user now, once, that they should continue in a new terminal "
                       "window or type /clear. The handoff and session summary will carry the context.")
        emit_context("SessionStart", "\n\n".join(out))
        return

    for script, args in (("memory_index.py", ["build", "--quiet"]), ("obsidian_map.py", [])):
        try:
            subprocess.Popen([sys.executable, str(ROOT / ".claude" / "scripts" / script), *args],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except Exception:
            pass

    ps = plan_status()
    if ps:
        out.append("Plan status (docs/plan.md):\n" + ps)
    ls = last_summary()
    if ls:
        out.append(ls)
    fails = summary_failures()
    if fails:
        lines = [f"- session {sid[:8]} at {v.get('time', '?')}: {v.get('error', '')[:160]}\n  redo: python3 "
                 f".claude/scripts/summarize_session.py {v.get('transcript', '?')} {sid} retry" for sid, v in fails.items()]
        out.append("SESSION SUMMARY FAILED (tell Ioseb at the start, in one sentence, and offer to redo it; "
                   "'Not logged in' means he must run claude and /login first):\n" + "\n".join(lines))
    props = open_proposals()
    if props:
        lines = [f"- {name[:4]} [{status}] {title[:90]}" for name, status, title in props]
        extra = (" There are more than 8 waiting: suggest a short review session to decide them."
                 if sum(s == "proposed" for _, s, _ in props) > 8 else "")
        out.append("Open improvement proposals (memory/proposals/). Mention the 'proposed' ones to the user "
                   "once, briefly, when there is a natural pause; build 'approved' ones when asked." + extra
                   + "\n" + "\n".join(lines))
    if HANDOFF.exists() and time.time() - HANDOFF.stat().st_mtime < 7 * 86400:
        out.append(f"A handoff from an earlier session exists at memory/working/handoff.md "
                   f"(updated {time.strftime('%Y-%m-%d %H:%M', time.localtime(HANDOFF.stat().st_mtime))}). "
                   "Read it if the user is continuing that work.")
    if out:
        emit_context("SessionStart", "ProfitLens session brief (from hooks):\n\n" + "\n\n".join(out))


if __name__ == "__main__":
    main()
