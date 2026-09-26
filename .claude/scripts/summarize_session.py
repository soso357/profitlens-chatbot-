#!/usr/bin/env python3
"""Background session summarizer (ADR 0010). Started by session_end.py.

Usage: summarize_session.py <transcript.jsonl> <session_id> <reason> [--dry-run]

1. Condenses the transcript: what the user said, what Claude said, answers to
   questions, files changed. Tool output is dropped.
2. Runs a headless Claude call from a temporary folder (so project hooks do not
   fire again) to write a structured summary.
3. Saves memory/episodic/sessions/<date>-<hhmmss>-<id8>.md and any improvement
   proposals as memory/proposals/NNNN-<slug>.md with status 'proposed'.
4. Rebuilds the memory index.

A resumed session is summarized again only for the part after the last summary
(the line count is kept in memory/working/state/<id>.summary.json). An OS file lock
stops two runs for the same session from writing at once. A failed run is
recorded in memory/working/state/<id>.summary-failed.json, which the statusline and
the session brief show until a later run for that session succeeds.
"""
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import (GUARD_ENV, PROPOSALS, ROOT, SESSIONS, STATE, is_real_user_text, open_proposals,  # noqa: E402
                    scrub, session_state_path, set_summary_failure)

MIN_USER_MESSAGES = 3
MAX_CHARS = 90_000
MODEL = os.environ.get("PL_SUMMARY_MODEL", "sonnet")

PROMPT = """You are writing the end-of-session record for a software project: a website chat agent for ProfitLens, built with Claude Code by Ioseb (not a software engineer). Below is a condensed transcript of one Claude Code session. Tool output was removed.

Write the record in EXACTLY this format. Plain English, no em dashes or en dashes, no filler. Only state what the transcript supports. Never include secrets, API keys, passwords or personal data about website visitors.

---
title: <one line, what this session achieved>
phase: <build phase worked on, e.g. "Phase 0", "Phase 1", "Workflow">
outcome: <done | partial | blocked | exploration>
reviewed: no
---

## Goal
<1 to 3 sentences: what the user wanted>

## What was done
<bullets, concrete: files created or changed, things run and verified>

## Decisions
<bullets: each decision, the option chosen, who chose it. Write "None" if none>

## Problems and lessons
<bullets: mistakes, surprises, anything that should change how future sessions work. "None" if none>

## Open questions
<bullets: things waiting on Ioseb or the founders>

## Next steps
<numbered, the concrete next actions>

## Proposals
```json
[]
```

For "## Proposals": propose improvements to the project or to the development setup that the session revealed but the user did NOT explicitly ask for. Examples: a repeated manual task that should become a skill, a chatbot behaviour the spec does not cover, a missing guardrail or test, a rule Claude broke twice. Each item: {{"title": "...", "kind": "skill|rule|hook|spec|test|doc", "why": "evidence from this session", "what": "what would be created or changed"}}. At most 3. Use [] if nothing is clearly worth it. Do not repeat these existing proposals:
{existing}

Condensed transcript (session {sid}, ended because: {reason}):

{transcript}
"""


def condense(path, start_line=0):
    """Condense transcript lines from start_line on. Returns (text, user messages, files, total lines)."""
    tool_names, lines, user_count, files, n = {}, [], 0, set(), 0
    for n, raw in enumerate(open(path, errors="replace"), 1):
        if n <= start_line:
            continue
        try:
            e = json.loads(raw)
        except Exception:
            continue
        t, msg = e.get("type"), e.get("message") or {}
        content = msg.get("content")
        if t == "user" and not e.get("isMeta"):
            if is_real_user_text(content):
                user_count += 1
                lines.append(f"USER: {content.strip()[:6000]}")
            elif isinstance(content, list):
                for b in content:
                    if b.get("type") == "tool_result" and tool_names.get(b.get("tool_use_id")) == "AskUserQuestion":
                        c = b.get("content")
                        text = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
                        lines.append(f"USER ANSWERED: {text[:2000]}")
        elif t == "assistant" and isinstance(content, list):
            for b in content:
                if b.get("type") == "text" and b.get("text", "").strip():
                    lines.append(f"CLAUDE: {b['text'].strip()[:3000]}")
                elif b.get("type") == "tool_use":
                    name, inp = b.get("name", ""), b.get("input") or {}
                    tool_names[b.get("id")] = name
                    if name in ("Write", "Edit", "NotebookEdit") and inp.get("file_path"):
                        files.add(inp["file_path"].replace(str(ROOT) + "/", ""))
                    elif name == "AskUserQuestion":
                        qs = [q.get("question", "") for q in inp.get("questions", [])]
                        lines.append("CLAUDE ASKED: " + " | ".join(qs))
                    elif name == "Bash" and inp.get("description"):
                        lines.append(f"(ran: {inp['description'][:120]})")
    text = "\n".join(lines)
    if files:
        text += "\n\nFILES WRITTEN OR EDITED:\n" + "\n".join(sorted(files))
    if len(text) > MAX_CHARS:
        half = MAX_CHARS // 2
        text = text[:half] + "\n\n[... middle of session omitted ...]\n\n" + text[-half:]
    return scrub(text), user_count, len(files), n


def next_proposal_number():
    nums = [int(p.name[:4]) for p in PROPOSALS.glob("[0-9][0-9][0-9][0-9]-*.md")]
    return max(nums, default=0) + 1


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:50]


def save_proposals(summary_text, session_file, sid):
    m = re.search(r"## Proposals\s*```json\s*(.*?)```", summary_text, re.S)
    if not m:
        return []
    try:
        items = json.loads(m.group(1))
    except Exception:
        return []
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)
    saved = []
    numbering = open(STATE / "proposals.lock", "w")
    fcntl.flock(numbering, fcntl.LOCK_EX)  # one run at a time picks numbers; released on exit, even after a crash
    for it in items[:3]:
        if not isinstance(it, dict) or not it.get("title"):
            continue
        p = PROPOSALS / f"{next_proposal_number():04d}-{slugify(it['title'])}.md"
        p.write_text(
            f"---\ntitle: {it['title']}\nstatus: proposed\nkind: {it.get('kind', 'other')}\n"
            f"source: {session_file}\ncreated: {time.strftime('%Y-%m-%d')}\n---\n\n"
            f"## Why\n{it.get('why', '')}\n\n## What\n{it.get('what', '')}\n\n## Decision\n(pending Ioseb)\n"
        )
        saved.append(p.name)
    numbering.close()
    return saved


def progress_path(sid):
    return session_state_path(sid).with_suffix(".summary.json")


def acquire_lock(sid):
    """An OS lock on <id>.summary.lock: the system releases it when the process ends, even after a crash,
    so there is never a stale lock to clear. Returns the open file, or None if another run holds it."""
    STATE.mkdir(parents=True, exist_ok=True)
    f = open(session_state_path(sid).with_suffix(".summary.lock"), "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except BlockingIOError:
        f.close()
        return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    transcript, sid, reason = (args + ["", "unknown", "other"])[:3]
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if dry:
        return summarize(transcript, sid, reason, stamp, dry=True)
    lock = acquire_lock(sid)
    if not lock:
        print(f"{stamp} skip {sid}: another summary of this session is running")
        return
    try:
        summarize(transcript, sid, reason, stamp)
    except Exception as e:  # never fail silently
        print(f"{stamp} FAILED {sid}: {e!r}")
        set_summary_failure(sid, {"time": stamp, "error": repr(e)[:300], "transcript": transcript})
    finally:
        lock.close()


def summarize(transcript, sid, reason, stamp, dry=False):
    try:
        start = int(json.loads(progress_path(sid).read_text()).get("lines", 0))
    except Exception:
        start = 0
    text, user_count, n_files, total = condense(transcript, start)
    if user_count < MIN_USER_MESSAGES and n_files == 0 and not dry:
        print(f"{stamp} skip {sid}: {user_count} new user messages and no files changed")
        return
    existing = "\n".join(f"- {t}" for _, _, t in open_proposals()) or "(none)"
    prompt = PROMPT.format(existing=existing, sid=sid[:8], reason=reason, transcript=text)
    if dry:
        print(prompt[:3000], f"\n... [{len(prompt)} chars, {user_count} user messages]")
        return

    env = dict(os.environ, **{GUARD_ENV: "1"})
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            ["claude", "-p", "--model", MODEL, "--no-session-persistence", "--tools", "", "--output-format", "text"],
            input=prompt, capture_output=True, text=True, cwd=tmp, env=env, timeout=600,
        )
    if r.returncode != 0 or "## Next steps" not in r.stdout:
        err = f"rc={r.returncode} {r.stderr.strip()[:300]} {r.stdout.strip()[:200]}".strip()
        print(f"{stamp} FAILED {sid}: {err}")
        set_summary_failure(sid, {"time": stamp, "error": err, "transcript": transcript})
        return
    body = scrub(r.stdout.strip())
    body = body.replace("—", ", ").replace("–", " to ")
    if not body.startswith("---"):
        body = body[body.find("---"):]
    body = close_header(body)
    SESSIONS.mkdir(parents=True, exist_ok=True)
    out = SESSIONS / f"{time.strftime('%Y-%m-%d-%H%M%S')}-{sid[:8]}.md"
    part = f"\npart: continues an earlier summary of this session (transcript line {start + 1} on)" if start else ""
    body = body.replace("reviewed: no", f"reviewed: no\nsession: {sid}\nended: {stamp}\nreason: {reason}{part}", 1)
    out.write_text(body + "\n")
    progress_path(sid).write_text(json.dumps({"lines": total, "summary": out.name}))
    set_summary_failure(sid, None)
    props = save_proposals(body, out.name, sid)
    subprocess.run([sys.executable, str(Path(__file__).with_name("memory_index.py")), "build", "--quiet"])
    print(f"{stamp} wrote {out.relative_to(ROOT)}; proposals: {props or 'none'}")


def close_header(body):
    """The model sometimes leaves out the closing --- of the header; without it no field
    (reviewed, ended) can be read, and every summary looks unreviewed."""
    first = body.find("\n## ")
    if body.startswith("---\n") and first != -1 and "\n---" not in body[3:first]:
        body = body[:first] + "\n---" + body[first:]
    return body


if __name__ == "__main__":
    main()
