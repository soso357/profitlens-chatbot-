"""Offline checks of the spec rules (foundation v2 step 4, ADR 0025): the real spec's structure,
and the checker and draft hook on small made up specs. Run: python3 -m tests.check_spec"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "scripts"))
import spec_check as sc  # noqa: E402

failures = 0


def check(name, ok):
    global failures
    failures += not ok
    print(f"  [{'OK' if ok else 'FAILED'}] {name}")


SPEC = """# Spec

Version: {version}
Status: {status}
Approved by: Ioseb
Date: 2026-09-27

## 2. Rules

- **R1 One.** Only approved answers.
- **R2 Two.** Wording FOUNDER TO CONFIRM.

## 3. Behaviour

| Id | Situation | Required behaviour | Source file |
|---|---|---|---|
| B1 | First reply | Disclosure | x |

## 8. Acceptance checks

| Id | Check |
|---|---|
{rows}
"""
ROWS = "| R1 | tests/check_guardrails.py |\n| R2 | manual: founders read transcripts; weekly |\n| B1 | none yet |"


def spec(version="1.0", status="Approved", rows=ROWS):
    return SPEC.format(version=version, status=status, rows=rows)


def plan(note):
    return f"# Plan\n\n## Phase notes\n\n{note}\n\n---\n\n## Phase 0\n"


print("The real spec:")
real = subprocess.run([sys.executable, str(ROOT / ".claude" / "scripts" / "spec_check.py")], capture_output=True,
                      text=True, stdin=subprocess.DEVNULL)
check("docs/spec.md passes the structure check", real.returncode == 0)
if real.returncode:
    print(real.stdout)

print("Structure:")
check("a complete spec has no problems", sc.structure_problems(spec(), plan("")) == [])
check("missing header is found", any("header" in p for p in sc.structure_problems(
    spec().replace("Version: 1.0\n", "").replace("Status: Approved\n", ""), plan(""))))
check("an id without an acceptance row is found", any("B1 has no row" in p for p in sc.structure_problems(
    spec(rows=ROWS.replace("| B1 | none yet |", "")), plan(""))))
check("a test that does not exist is found", any("tests/nope.py" in p for p in sc.structure_problems(
    spec(rows=ROWS.replace("tests/check_guardrails.py", "tests/nope.py")), plan(""))))
check("a conversation number that does not exist is found", any("#99" in p for p in sc.structure_problems(
    spec(rows=ROWS.replace("tests/check_guardrails.py", "tests/conversations.md#99")), plan(""))))
check("an existing conversation number is fine", sc.structure_problems(
    spec(rows=ROWS.replace("tests/check_guardrails.py", "tests/conversations.md#3")), plan("")) == [])

print("Phase notes:")
old = "### Phase 4 widget (2026-09-23)\n1. no citation needed before step 4"
check("old notes need no citation", sc.structure_problems(spec(), plan(old)) == [])
new = "### Phase 6 digest (2026-09-28)\nSpec version 1.0, covers R1, B1\n1. x"
check("new note citing the approved version is fine", sc.structure_problems(spec(), plan(new)) == [])
check("new note without a citation is found", any("does not start" in p for p in sc.structure_problems(
    spec(), plan("### Phase 6 digest (2026-09-28)\n1. x"))))
check("new note citing an old version is found", any("cites spec 0.9" in p for p in sc.structure_problems(
    spec(), plan(new.replace("1.0", "0.9")))))
check("new note while the spec is Draft is found", any("Draft" in p for p in sc.structure_problems(
    spec(status="Draft"), plan(new))))
check("new note covering a FOUNDER TO CONFIRM id is found", any("R2 is FOUNDER TO CONFIRM" in p for p in
                                                               sc.structure_problems(spec(), plan(new.replace("B1", "B1, R2")))))
check("foundation notes (not '### Phase') are not checked", sc.structure_problems(
    spec(), plan("### Foundation v2 step 9 (2026-09-30)\n1. x")) == [])

print("Readiness:")
check("approved spec, known ids: ready", sc.readiness_problems(["R1", "B1"], spec()) == [])
check("Draft spec: not ready", any("not Approved" in p for p in sc.readiness_problems(["R1"], spec(status="Draft"))))
check("unknown id: not ready", any("R9 is not in the spec" in p for p in sc.readiness_problems(["R9"], spec())))

print("Draft hook:")
tmp = Path(tempfile.mkdtemp(prefix="profitlens-spec-"))
(tmp / "docs").mkdir()
f = tmp / "docs" / "spec.md"
env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp))


def hook(inp):
    return subprocess.run([sys.executable, str(ROOT / ".claude" / "scripts" / "spec_check.py"), "hook"], env=env,
                          input=json.dumps({"tool_name": "Edit", "tool_input": inp}), capture_output=True, text=True)


f.write_text(spec())
out = hook({"file_path": str(f), "old_string": "Only approved", "new_string": "Only the approved"})
check("editing an approved spec makes it Draft and tells Claude", "Status: Draft" in f.read_text()
      and "Draft again" in out.stdout)
f.write_text(spec(status="Draft"))
hook({"file_path": str(f), "old_string": "Status: Draft", "new_string": "Status: Approved"})
f.write_text(spec())  # the approval edit itself, as Claude would write it
hook({"file_path": str(f), "old_string": "Status: Draft", "new_string": "Status: Approved"})
check("the approval edit itself stays Approved", "Status: Approved" in f.read_text())
other = tmp / "docs" / "plan.md"
other.write_text("x")
f.write_text(spec())
hook({"file_path": str(other), "old_string": "x", "new_string": "y"})
check("editing another file leaves the spec alone", "Status: Approved" in f.read_text())

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
raise SystemExit(bool(failures))
