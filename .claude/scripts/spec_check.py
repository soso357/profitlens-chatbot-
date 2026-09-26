#!/usr/bin/env python3
"""Spec checks (foundation v2 step 4, ADR 0025).

  spec_check.py              structure: header, every R/B/G id has an acceptance row, named tests exist,
                             phase notes cite the approved version (exit 1 on a problem)
  spec_check.py ready IDS    readiness before a phase note: spec Approved, each id exists, has a check
                             row, and is not FOUNDER TO CONFIRM
  spec_check.py hook         PostToolUse hook: an edit to an Approved spec sets it back to Draft
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT, read_hook_input  # noqa: E402

SPEC = ROOT / "docs" / "spec.md"
PLAN = ROOT / "docs" / "plan.md"
CITE_FROM = "2026-09-27"  # phase notes from this date on must cite an approved spec version
ID = re.compile(r"\b([RBG]\d{1,2})\b")


def header(text):
    return {k.lower(): v.strip() for k, v in re.findall(r"^(Version|Status|Approved by|Date):\s*(.*)$", text[:600], re.M)}


def requirement_ids(text):
    """Ids defined in sections 2 to 4: **R1 ...** bullets and | B1 | / | G1 | table rows."""
    body = text.split("## 8. Acceptance checks")[0]
    ids = set(re.findall(r"^- \*\*([R]\d+) ", body, re.M)) | set(re.findall(r"^\| ([BG]\d+) \|", body, re.M))
    return ids


def requirement_text(text, rid):
    body = text.split("## 8. Acceptance checks")[0]
    m = re.search(rf"^(- \*\*{rid} .*|\| {rid} \|.*)$", body, re.M)
    return m.group(1) if m else ""


def acceptance(text):
    section = text.split("## 8. Acceptance checks", 1)[1] if "## 8. Acceptance checks" in text else ""
    return dict(re.findall(r"^\| ([RBG]\d+) \| (.*?) \|$", section, re.M))


def missing_tests(check):
    """Named test references in one acceptance cell that do not exist."""
    out = []
    if check.strip().startswith(("manual:", "none yet")):
        return out
    for ref in [c.strip() for c in check.split(";")]:
        if not ref or ref.startswith(("manual:", "none yet")):
            continue
        path, _, conv = ref.partition("#")
        f = ROOT / path
        if not f.exists():
            out.append(ref)
        elif conv and not re.search(rf"^## {re.escape(conv)}\.", f.read_text(), re.M):
            out.append(ref)
    return out


def phase_notes(plan_text):
    """[(heading, body)] of the per phase notes."""
    parts = re.split(r"^(### .*)$", plan_text.split("## Phase notes", 1)[-1].split("\n---")[0], flags=re.M)
    return [(parts[i], parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def structure_problems(spec_text=None, plan_text=None):
    spec_text = spec_text if spec_text is not None else SPEC.read_text()
    plan_text = plan_text if plan_text is not None else (PLAN.read_text() if PLAN.exists() else "")
    problems = []
    h = header(spec_text)
    if not h.get("version") or h.get("status") not in ("Draft", "Approved"):
        problems.append("spec header needs 'Version: X' and 'Status: Draft' or 'Status: Approved'")
    ids, acc = requirement_ids(spec_text), acceptance(spec_text)
    for rid in sorted(ids - set(acc), key=lambda x: (x[0], int(x[1:]))):
        problems.append(f"{rid} has no row in section 8 (Acceptance checks)")
    for rid in sorted(set(acc) - ids):
        problems.append(f"section 8 has {rid}, which is not a requirement")
    for rid, check in acc.items():
        for ref in missing_tests(check):
            problems.append(f"{rid}: {ref} does not exist")
    for heading, body in phase_notes(plan_text):
        date = re.search(r"\d{4}-\d{2}-\d{2}", heading)
        if not heading.startswith("### Phase") or not date or date.group(0) < CITE_FROM:
            continue
        m = re.search(r"Spec version ([\d.]+), covers (.*)", body)
        if not m:
            problems.append(f"phase note '{heading[4:60]}' does not start with 'Spec version X, covers ...'")
        elif h.get("status") != "Approved" or m.group(1) != h.get("version"):
            problems.append(f"phase note '{heading[4:60]}' cites spec {m.group(1)}, but the approved spec is "
                            f"{h.get('version') if h.get('status') == 'Approved' else 'none (spec is Draft)'}")
        else:
            problems += [f"phase note '{heading[4:60]}': {p}" for p in readiness_problems(ID.findall(m.group(2)), spec_text)]
    return problems


def readiness_problems(ids, spec_text=None):
    spec_text = spec_text if spec_text is not None else SPEC.read_text()
    h, known, acc = header(spec_text), requirement_ids(spec_text), acceptance(spec_text)
    problems = [] if h.get("status") == "Approved" else ["spec is not Approved: Ioseb approves it before planning"]
    for rid in ids:
        if rid not in known:
            problems.append(f"{rid} is not in the spec")
        elif "FOUNDER TO CONFIRM" in requirement_text(spec_text, rid):
            problems.append(f"{rid} is FOUNDER TO CONFIRM: not decided, cannot be planned")
        elif rid not in acc:
            problems.append(f"{rid} has no acceptance check")
    return problems


def hook():
    """An edit to the approved spec makes it Draft again, unless the edit itself is the approval."""
    data = read_hook_input()
    inp = data.get("tool_input") or {}
    try:
        if Path(inp.get("file_path", "")).resolve() != SPEC.resolve():
            return
    except Exception:
        return
    new_text = inp.get("new_string") or inp.get("content") or ""
    if "Status: Approved" in new_text:  # this edit is the approval itself
        return
    text = SPEC.read_text()
    if header(text).get("status") == "Approved":
        text = re.sub(r"^Status: Approved$", "Status: Draft", text, count=1, flags=re.M)
        text = re.sub(r"^Approved by: .*$", "Approved by: (changed after approval, waiting for Ioseb)", text, count=1,
                      flags=re.M)
        SPEC.write_text(text)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
              "docs/spec.md was Approved and has been changed, so it is Draft again (ADR 0025). Tell Ioseb in one "
              "line; he approves the next version."}}))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "structure"
    if cmd == "hook":
        return hook()
    problems = readiness_problems(sys.argv[2:]) if cmd == "ready" else structure_problems()
    if cmd == "structure":
        acc = acceptance(SPEC.read_text())
        todo = sorted((r for r, c in acc.items() if c.startswith("none yet")), key=lambda x: (x[0], int(x[1:])))
        if todo:
            print("No check yet (not a failure): " + ", ".join(todo))
    for p in problems:
        print("PROBLEM: " + p)
    print("ALL CHECKS PASSED" if not problems else f"{len(problems)} PROBLEM(S)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
