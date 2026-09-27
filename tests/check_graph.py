"""Offline checks of the context graph (foundation v2 step 6): the real project has no broken links
and its known links are found; the builder works on a small made up project.
Run: python3 -m tests.check_graph"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "scripts"))
import graph  # noqa: E402

failures = 0


def check(name, ok):
    global failures
    failures += not ok
    print(f"  [{'OK' if ok else 'FAILED'}] {name}")


print("The real project:")
check("no broken links", graph.problems(ROOT) == [])
e = graph.edges(ROOT)
check("G1 is enforced by app/guardrails.py", ("app/guardrails.py", "implements", "G1") in e)
check("R2 is proved by tests/check_guardrails.py", ("R2", "proved_by", "tests/check_guardrails.py") in e)
check("ADR 0022 supersedes ADR 0012", ("0022", "supersedes", "0012") in e)
ids = graph.spec_ids(ROOT)
implemented = {d for s, r, d in e if r == "implements"}
check("every Implements line names a real spec id", implemented <= set(ids))
w = graph.what("R2", ROOT)
check("what R2 shows code and tests", "enforced in code by: app/guardrails.py" in w and "proved by" in w)
check("what 0012 shows it was superseded", "superseded by: ADR 0022" in graph.what("12", ROOT))

print("A small made up project:")
tmp = Path(tempfile.mkdtemp(prefix="profitlens-graph-"))
(tmp / "docs" / "adr").mkdir(parents=True)
(tmp / "app").mkdir()
(tmp / "tests").mkdir()
(tmp / "docs" / "spec.md").write_text(
    "# Spec\n\n- **R1 Only approved answers.** (ADR 0003)\n- **R2 No figures.**\n\n"
    "| Id | Situation | Required behaviour | Source |\n|---|---|---|---|\n| B1 | First reply | Disclosure | x |\n\n"
    "## 8. Acceptance checks\n\n| Id | Check |\n|---|---|\n| R1 | tests/check_a.py |\n| R2 | none yet |\n"
    "| B1 | manual: founders |\n")
(tmp / "docs" / "adr" / "0001-approved.md").write_text("# ADR 0001\n\n- Status: Accepted\n\n## Decision\n\nOnly R1.\n")
(tmp / "docs" / "adr" / "0002-new.md").write_text(
    "# ADR 0002\n\n- Status: Accepted\n- Links: decides B1\n\n## Decision\n\nText naming R2 that is not a link.\n")
(tmp / "docs" / "adr" / "0003-old.md").write_text("# ADR 0003\n\n- Status: Superseded by 0002\n\n## Decision\n\nx\n")
(tmp / "app" / "guard.py").write_text('"""Guard.\nImplements: R1, R9\n"""\n# see ADR 0007\n')
(tmp / "tests" / "check_a.py").write_text("# proves R1\n")
e = graph.edges(tmp)
check("proved_by from spec section 8", ("R1", "proved_by", "tests/check_a.py") in e)
check("'none yet' and 'manual' are not links", not any(s in ("R2", "B1") and r == "proved_by" for s, r, d in e))
check("implements from the docstring line", ("app/guard.py", "implements", "R1") in e)
check("decides from the spec line citing an ADR", ("0003", "decides", "R1") in e)
check("decides from the ADR's Decision section", ("0001", "decides", "R1") in e)
check("a Links line wins over ids in the Decision text", ("0002", "decides", "B1") in e and ("0002", "decides", "R2") not in e)
check("supersedes from the status line", ("0002", "supersedes", "0003") in e)
p = graph.problems(tmp)
check("implementing an id not in the spec is a broken link", any("R9" in x for x in p))
check("mentioning an ADR that does not exist is a broken link", any("ADR 0007" in x for x in p))
no_code, no_test = graph.orphans(tmp)
check("orphans: no code for R2 and B1, no test for R2 and B1", set(no_code) == {"R2", "B1"} and set(no_test) == {"R2", "B1"})
check("what on an unknown node says so", "no links" in graph.what("G9", tmp))

print("Obsidian notes:")
vault = tmp / "vault"
(vault / "requirements").mkdir(parents=True)
(vault / "requirements" / "My own note.md").write_text("Ioseb's thoughts on R2\n")
(vault / "requirements" / "R99.md").write_text(f"# R99\n\n{graph.MARK}\n")
graph.obsidian_notes(vault, lambda rel: f"PROFITLENS CHATBOT/{rel}")
check("a note Ioseb wrote in requirements/ is kept", (vault / "requirements" / "My own note.md").exists())
check("old generated notes are replaced", not (vault / "requirements" / "R99.md").exists()
      and (vault / "requirements" / "R2.md").exists())

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
raise SystemExit(bool(failures))
