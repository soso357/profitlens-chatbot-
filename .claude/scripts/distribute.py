#!/usr/bin/env python3
"""Sort a session summary into the project files (foundation v2 step 2, ADR 0022).

Usage: distribute.py <summary.md>     (run by summarize_session.py after each summary)

Reads the summary's "## Routed" JSON block:
  done, open_questions, waiting  -> docs/progress.md, automatically
  lessons                        -> memory/procedural/lessons.md, automatically;
                                    a lesson seen before becomes a rule proposal
  decisions                      -> a proposal "record this decision" if neither docs/build-log.md
                                    nor an ADR has a matching passage
  changes (plan, spec, ADR, rule) -> proposals; those files are never edited here
Every automatic line ends with "(from <summary file>)" so a wrong one can be traced and removed.
Items already present are skipped. One run at a time (OS file lock), also across worktrees.
A failure is kept per summary in memory/working/state/distribute-failed/<summary>.json (shown by
the resume brief) until that summary is sorted successfully.
"""
import fcntl
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import MAIN_ROOT, MEMORY, STATE, similar, words  # noqa: E402

PROGRESS = MAIN_ROOT / "docs" / "progress.md"
BUILD_LOG = MAIN_ROOT / "docs" / "build-log.md"
LESSONS = MEMORY / "procedural" / "lessons.md"
FAILED = STATE / "distribute-failed"
SAME = 0.6          # word overlap at which two lines count as the same item
SAME_LESSON = 0.5
MAX_PROPOSALS = 5   # per summary, so a bad summary cannot flood the queue
SECTIONS = {"done": "## Done (newest first)", "open_questions": "## Open questions", "waiting": "## Waiting on people"}


# question and framing words say nothing about what was decided
FRAMING = {"what", "which", "when", "where", "whether", "handle", "apply", "decide", "decision", "choose", "chosen",
           "ioseb", "founders", "should", "option", "options", "make", "made", "from", "with", "that", "this", "into",
           "request", "answers", "since", "phase", "step"}


def content_words(text):
    return {w for w in words(text) if w not in FRAMING and not w.isdigit()}


def share(a, b):
    """Share of the words in a that appear in b; a word matches its other forms ('skip', 'skipped')."""
    if not a:
        return 1.0
    hits = sum(1 for x in a if any(min(len(x), len(y)) >= 4 and x[:4] == y[:4] and
                                   (y.startswith(x[:5]) or x.startswith(y[:5])) for y in b))
    return hits / len(a)


def recorded(topic, chosen, passage):
    """True when one build log line or ADR decision names the topic AND most of what was chosen.
    Errs towards 'not recorded': a spare proposal costs a click, a lost decision costs more
    ('Kill switch: build it now' must not match 'Kill switch postponed')."""
    t, c, p = content_words(topic), content_words(chosen), content_words(passage)
    return len(t | c) >= 2 and share(t, p) >= 0.5 and share(c, p) >= 0.67


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
            "waiting": [f"- {t} {src}" for t in (
                (f"{i.get('who')}: {i.get('what')}" if isinstance(i, dict) and i.get("who") and i.get("what")
                 else as_text(i, ["who", "what"])) for i in items.get("waiting") or []) if t],
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
    log = [l for l in (BUILD_LOG.read_text().splitlines() if BUILD_LOG.exists() else []) if l.startswith("- ")]
    for adr in sorted((MAIN_ROOT / "docs" / "adr").glob("[0-9]*.md")):  # decisions recorded as ADRs count too
        text = adr.read_text()
        title = text.splitlines()[0] if text else ""
        m = re.search(r"## Decision\s*\n(.*?)(\n## |\Z)", text, re.S)
        log.append(title + " " + (m.group(1) if m else ""))
    for d in items.get("decisions") or []:
        text = as_text(d, ["decision", "chosen"])  # who decided is not content
        topic, chosen = (d.get("decision", ""), d.get("chosen", "")) if isinstance(d, dict) else (text, "")
        if text and not any(recorded(topic, chosen, l) for l in log):
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


def record_failure(summary_name, info):
    """Keep (info given) or clear (None) the sorting failure of one summary."""
    f = FAILED / f"{summary_name}.json"
    if info:
        FAILED.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(info))
    else:
        f.unlink(missing_ok=True)


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
        record_failure(result["summary"], None if result["ok"] else result)
    print(json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
