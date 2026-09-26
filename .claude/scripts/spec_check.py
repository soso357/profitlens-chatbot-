#!/usr/bin/env python3
"""Spec checks (foundation v2 step 4, ADR 0025).

  spec_check.py              structure: header, every R/B/G id has an acceptance row, named tests exist,
                             phase notes cite the approved version (exit 1 on a problem)
  spec_check.py ready IDS    readiness before a phase note: spec Approved, each id exists, has a check
                             row, and is not blocked by a FOUNDER TO CONFIRM item
  spec_check.py approve      only after Ioseb said approved: next version, Status Approved, date, and a
                             fingerprint of the text
  spec_check.py hook         PostToolUse hook: if an Approved spec's text no longer matches its
                             fingerprint (any tool: Edit, MultiEdit, Write), it becomes Draft again
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT, read_hook_input  # noqa: E402

SPEC = ROOT / "docs" / "spec.md"
PLAN = ROOT / "docs" / "plan.md"
LEGACY = "[before spec versions]"  # phase notes written before ADR 0025 carry this tag and need no citation
HEADER_KEYS = ("Version", "Status", "Approved by", "Date", "Fingerprint")
ID = re.compile(r"\b([RBG]\d{1,2})\b")


def header(text):
    return {k.lower(): v.strip() for k, v in
            re.findall(r"^(Version|Status|Approved by|Date|Fingerprint):\s*(.*)$", text[:800], re.M)}


def fingerprint(text):
    """Hash of the spec without its header lines: any change to the content changes it."""
    body = "\n".join(l for l in text.splitlines() if not re.match(rf"^({'|'.join(HEADER_KEYS)}):", l))
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def changed_after_approval(text):
    h = header(text)
    return h.get("status") == "Approved" and h.get("fingerprint") != fingerprint(text)


def set_header(text, key, value):
    if re.search(rf"^{key}:.*$", text, re.M):
        return re.sub(rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.M)
    return re.sub(r"^(Date:.*)$", rf"\1\n{key}: {value}", text, count=1, flags=re.M)


def blocking_items(text, rid):
    """FOUNDER TO CONFIRM lines, anywhere after the preamble, that name this id or are its own line."""
    body = text.split("## 1.", 1)[-1]
    own = requirement_text(text, rid)
    return [l for l in body.splitlines() if "FOUNDER TO CONFIRM" in l and (l == own or re.search(rf"\b{rid}\b", l))]


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
    if changed_after_approval(spec_text):
        problems.append("spec says Approved but its text changed since approval (fingerprint): it must be Draft")
    for line in spec_text.split("## 1.", 1)[-1].splitlines():
        if "FOUNDER TO CONFIRM" in line and not ID.search(line):
            problems.append(f"FOUNDER TO CONFIRM item names no id it blocks: {line.strip()[:70]}")
    ids, acc = requirement_ids(spec_text), acceptance(spec_text)
    for rid in sorted(ids - set(acc), key=lambda x: (x[0], int(x[1:]))):
        problems.append(f"{rid} has no row in section 8 (Acceptance checks)")
    for rid in sorted(set(acc) - ids):
        problems.append(f"section 8 has {rid}, which is not a requirement")
    for rid, check in acc.items():
        for ref in missing_tests(check):
            problems.append(f"{rid}: {ref} does not exist")
    for heading, body in phase_notes(plan_text):
        if not heading.startswith("### Phase") or LEGACY in heading:
            continue
        m = re.search(r"Spec version ([\d.]+), covers (.*)", body)
        if not m:
            problems.append(f"phase note '{heading[4:60]}' does not start with 'Spec version X, covers ...'")
        elif h.get("status") != "Approved" or changed_after_approval(spec_text) or m.group(1) != h.get("version"):
            problems.append(f"phase note '{heading[4:60]}' cites spec {m.group(1)}, but the approved spec is "
                            f"{h.get('version') if h.get('status') == 'Approved' else 'none (spec is Draft)'}")
        else:
            problems += [f"phase note '{heading[4:60]}': {p}" for p in readiness_problems(ID.findall(m.group(2)), spec_text)]
    return problems


def readiness_problems(ids, spec_text=None):
    spec_text = spec_text if spec_text is not None else SPEC.read_text()
    h, known, acc = header(spec_text), requirement_ids(spec_text), acceptance(spec_text)
    problems = [] if h.get("status") == "Approved" and not changed_after_approval(spec_text) else [
        "spec is not Approved: Ioseb approves it before planning"]
    if not ids:
        problems.append("no requirement ids given (for example: ready R8 G5)")
    for rid in ids:
        if rid not in known:
            problems.append(f"{rid} is not in the spec")
        elif blocking_items(spec_text, rid):
            problems.append(f"{rid} is blocked by a FOUNDER TO CONFIRM item: not decided, cannot be planned")
        elif rid not in acc:
            problems.append(f"{rid} has no acceptance check")
    return problems


def hook():
    """Any tool that leaves an Approved spec whose text no longer matches its fingerprint makes it Draft.
    Works the same for Edit, MultiEdit and Write, because it compares the file itself."""
    data = read_hook_input()
    inp = data.get("tool_input") or {}
    try:
        if Path(inp.get("file_path", "")).resolve() != SPEC.resolve():
            return
    except Exception:
        return
    text = SPEC.read_text()
    if changed_after_approval(text):
        text = set_header(set_header(text, "Status", "Draft"), "Approved by", "(changed after approval, waiting for Ioseb)")
        SPEC.write_text(text)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
              "docs/spec.md was Approved and its text changed, so it is Draft again (ADR 0025). Tell Ioseb in one "
              "line; when he approves, run: python3 .claude/scripts/spec_check.py approve"}}))


def approve():
    """Run only after Ioseb said approved. A spec approved before gets the next minor version."""
    text = SPEC.read_text()
    h = header(text)
    version = h.get("version", "1.0")
    if h.get("fingerprint"):  # approved before, then changed: next version
        major, _, minor = version.partition(".")
        version = f"{major}.{int(minor or 0) + 1}"
    for key, value in (("Version", version), ("Status", "Approved"), ("Approved by", "Ioseb"),
                       ("Date", time.strftime("%Y-%m-%d"))):
        text = set_header(text, key, value)
    text = set_header(text, "Fingerprint", fingerprint(text))
    SPEC.write_text(text)
    print(f"spec {version} Approved")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "structure"
    if cmd == "hook":
        return hook()
    if cmd == "approve":
        return approve()
    problems = readiness_problems(ID.findall(" ".join(sys.argv[2:]))) if cmd == "ready" else structure_problems()
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
