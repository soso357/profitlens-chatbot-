#!/usr/bin/env python3
"""Sort a session summary into the project files (foundation v2 step 2, ADR 0022).

Usage: distribute.py <summary.md>     (run by summarize_session.py after each summary)

Reads the summary's "## Routed" JSON block:
  done, open_questions, waiting  -> docs/progress.md, automatically
  lessons                        -> memory/procedural/lessons.md, automatically;
                                    a lesson seen before becomes a rule proposal
  decisions                      -> a proposal "record this decision" if docs/build-log.md
                                    has no matching line
  changes (plan, spec, ADR, rule) -> proposals; those files are never edited here
Every automatic line ends with "(from <summary file>)" so a wrong one can be traced and removed.
Items already present are skipped. One run at a time (OS file lock), also across worktrees.
The result is kept in memory/working/state/distribute-last.json for the resume brief.
"""
import fcntl
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import MAIN_ROOT, MEMORY, STATE, similar  # noqa: E402

PROGRESS = MAIN_ROOT / "docs" / "progress.md"
BUILD_LOG = MAIN_ROOT / "docs" / "build-log.md"
LESSONS = MEMORY / "procedural" / "lessons.md"
LAST = STATE / "distribute-last.json"
SAME = 0.6          # word overlap at which two lines count as the same item
SAME_LESSON = 0.5
MAX_PROPOSALS = 5   # per summary, so a bad summary cannot flood the queue
SECTIONS = {"done": "## Done (newest first)", "open_questions": "## Open questions", "waiting": "## Waiting on people"}


def routed_block(text):
    """(items, error). No block at all is not an error (older summaries have none)."""
    m = re.search(r"## Routed\s*```json\s*(.*?)```", text, re.S)
    if not m:
        return None, None
    try:
        items = json.loads(m.group(1))
    except Exception as e:
        return None, f"Routed block is not valid JSON: {e}"
    if not isinstance(items, dict):
        return None, "Routed block is not a JSON object"
    return items, None


def as_text(item, keys):
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        parts = [str(item.get(k, "")).strip() for k in keys]
        return " ".join(p for p in parts if p)
    return ""


def section_lines(text, heading):
    start = text.find(heading)
    if start == -1:
        return start, start, []
    body_start = text.find("\n", start) + 1
    nxt = text.find("\n## ", body_start)
    end = len(text) if nxt == -1 else nxt + 1
    return body_start, end, [l for l in text[body_start:end].splitlines() if l.startswith("- ")]


def add_to_progress(text, key, new_lines):
    heading = SECTIONS[key]
    start, end, existing = section_lines(text, heading)
    if start == -1:
        text = text.rstrip("\n") + f"\n\n{heading}\n\n"
        start, end, existing = section_lines(text, heading)
    added = [l for l in new_lines if not any(similar(l, e, SAME) for e in existing)]
    added = [l for i, l in enumerate(added) if not any(similar(l, x, SAME) for x in added[:i])]
    if not added:
        return text, 0
    block = "".join(l + "\n" for l in added)
    body = text[start:end]
    if key == "done":  # newest first: right under the heading
        lead = len(body) - len(body.lstrip("\n"))
        body = body[:lead] + block + body[lead:]
    else:  # after the last item of the section
        last = body.rfind("\n- ")
        cut = body.find("\n", last + 1) + 1 if last != -1 else len(body.rstrip("\n")) + 1
        body = (body[:cut] + block + body[cut:]) if last != -1 else (body.rstrip("\n") + "\n\n" + block + "\n")
    return text[:start] + body + text[end:], len(added)


def distribute(summary_path):
    summary_path = Path(summary_path)
    items, error = routed_block(summary_path.read_text())
    if error or items is None:
        return {"ok": error is None, "error": error, "summary": summary_path.name}
    src = f"(from {summary_path.name})"
    today = time.strftime("%Y-%m-%d")
    result = {"ok": True, "summary": summary_path.name, "progress": 0, "lessons": 0, "proposals": []}

    # progress.md: done, open questions, people we wait on
    if PROGRESS.exists():
        text = PROGRESS.read_text()
        wanted = {
            "done": [f"- {today}: {t} {src}" for t in (as_text(i, ["text"]) for i in items.get("done") or []) if t],
            "open_questions": [f"- {q} ({w}) {src}" if w else f"- {q} {src}" for q, w in
                               ((as_text(i, ["question", "q"]), (i.get("who") if isinstance(i, dict) else "") or "")
                                for i in items.get("open_questions") or []) if q],
            "waiting": [f"- {t} {src}" for t in (as_text(i, ["who", "what"]) for i in items.get("waiting") or []) if t],
        }
        for key, lines in wanted.items():
            text, n = add_to_progress(text, key, lines)
            result["progress"] += n
        PROGRESS.write_text(text)

    proposals = []
    # lessons: new ones appended; a repeated one becomes a rule proposal
    if LESSONS.exists():
        lessons_text = LESSONS.read_text()
        existing = [l for l in lessons_text.splitlines() if l.startswith("- ")]
        new = []
        for lesson in (as_text(i, ["text"]) for i in items.get("lessons") or []):
            if not lesson:
                continue
            if any(similar(lesson, e, SAME_LESSON) for e in existing):
                proposals.append({"title": f"Make a rule: {lesson[:70]}", "kind": "rule",
                                  "why": f"The same lesson came up again in {summary_path.name}: {lesson}",
                                  "what": "A rule in .claude/rules/ or CLAUDE.md, or a hook, so it cannot happen a third time."})
            elif not any(similar(lesson, x, SAME_LESSON) for x in new):
                new.append(lesson)
        if new:
            LESSONS.write_text(lessons_text.rstrip("\n") + "\n" + "".join(f"- {today}: {l} {src}\n" for l in new))
            result["lessons"] = len(new)

    # decisions: only proposed for recording if the build log has no matching line
    log = BUILD_LOG.read_text().splitlines() if BUILD_LOG.exists() else []
    for d in items.get("decisions") or []:
        text = as_text(d, ["decision", "chosen", "by"])
        if text and not any(similar(text, l, 0.5) for l in log):
            proposals.append({"title": f"Record decision: {as_text(d, ['decision'])[:70] or text[:70]}", "kind": "decision",
                              "why": f"Made in {summary_path.name} but not found in docs/build-log.md: {text}",
                              "what": "Confirm with Ioseb, then a build-log line and, for a design choice, an ADR."})

    # changes to plan, spec, ADRs, rules: always a proposal, never an edit
    for c in items.get("changes") or []:
        if not isinstance(c, dict) or not c.get("what"):
            continue
        kind = c.get("file", "doc") if c.get("file") in ("plan", "spec", "adr", "rule") else "doc"
        proposals.append({"title": f"Change {kind}: {c['what'][:70]}", "kind": kind,
                          "why": c.get("why") or f"From {summary_path.name}", "what": c["what"]})

    if proposals:
        from summarize_session import write_proposals
        result["proposals"] = write_proposals(proposals[:MAX_PROPOSALS], summary_path.name)
    return result


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "distribute.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            result = distribute(sys.argv[1])
        except Exception as e:  # never fail silently
            result = {"ok": False, "error": repr(e)[:300], "summary": Path(sys.argv[1]).name}
        result["time"] = time.strftime("%Y-%m-%d %H:%M")
        LAST.write_text(json.dumps(result))
    print(json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
