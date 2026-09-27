#!/usr/bin/env python3
"""Context graph (foundation v2 step 6, ADR 0023 C4 option A).

Typed links between requirements (R, B, G ids in docs/spec.md), decisions (ADRs), code, tests,
incidents and proposals, built from what the files already say:
  proved_by    spec section 8 names the test that proves an id
  implements   an app file's docstring line "Implements: G1, G3"
  decides      an ADR's "- Links: decides R3, B1" line (new ADRs, template) or ids its Decision names
  supersedes   an ADR's "Superseded by NNNN" status
  mentions     any id or "ADR NNNN" named in code, docs, incidents, skills and rules
Stored in the search index (memory/index.sqlite, table edges) by memory_index.py build.

  graph.py what R2 | 0004 | app/guardrails.py   everything linked to it, grouped by relation
  graph.py orphans                             ids with no code or no test, broken links (exit 1 on a broken link)
  graph.py notes                               Obsidian: one note per requirement linking its ADRs, code, tests
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import MAIN_ROOT  # noqa: E402

ROOT = MAIN_ROOT  # the graph is shared by every worktree, like the index
ID = re.compile(r"\b([RBG]\d{1,2})\b")
ADR_REF = re.compile(r"\bADRs? (\d{4})\b")
MENTION_SOURCES = ["app/*.py", ".claude/scripts/*.py", "tests/*.py", "docs/*.md", "memory/incidents/*.md",
                   ".claude/skills/*/SKILL.md", ".claude/rules/*.md", "content/*.md", "CLAUDE.md", "REVIEW.md"]
# tools and tests that name ids and ADR numbers as examples or fixtures, not as real links
NOT_MENTIONS = {".claude/scripts/graph.py", ".claude/scripts/spec_check.py", ".claude/scripts/distribute.py",
                "tests/check_graph.py", "tests/check_spec.py", "tests/check_workflow.py"}
MARK = "Generated from the project by graph.py (rebuilt at every session start, edits here are lost)."
PROCESS_RULES = {"R7", "R10", "R11", "R12", "R13"}  # about how we work, not code in the chatbot


def spec_ids(root=None):
    root = root or ROOT
    try:
        text = (root / "docs" / "spec.md").read_text().split("## 8. Acceptance checks")[0]
    except Exception:
        return {}
    ids = {m.group(1): m.group(2).strip() for m in re.finditer(r"^- \*\*([R]\d+) (.*?)\*\*", text, re.M)}
    ids.update({m.group(1): m.group(2).strip() for m in re.finditer(r"^\| ([BG]\d+) \| (.*?) \|", text, re.M)})
    return ids


def adr_files(root):
    return {p.name[:4]: p for p in sorted((root / "docs" / "adr").glob("[0-9][0-9][0-9][0-9]-*.md"))}


def rel(root, p):
    return str(Path(p).relative_to(root))


def edges(root=None):
    """[(src, relation, dst)]. Nodes: requirement ids, ADR numbers (four digits), file paths."""
    root = root or ROOT
    ids, adrs, out = spec_ids(root), adr_files(root), []
    spec = (root / "docs" / "spec.md").read_text() if (root / "docs" / "spec.md").exists() else ""
    if "## 8. Acceptance checks" in spec:
        for rid, check in re.findall(r"^\| ([RBG]\d+) \| (.*?) \|$", spec.split("## 8. Acceptance checks", 1)[1], re.M):
            if not check.startswith(("manual:", "none yet")):
                for ref in [c.strip() for c in check.split(";") if c.strip()]:
                    out.append((rid, "proved_by", ref))
    for line in spec.split("## 8. Acceptance checks")[0].splitlines():  # a requirement citing its ADR
        m = re.match(r"^(?:- \*\*([R]\d+) |\| ([BG]\d+) \|)", line)
        if m:
            out += [(num, "decides", m.group(1) or m.group(2)) for num in dict.fromkeys(ADR_REF.findall(line))]
    for p in sorted((root / "app").glob("*.py")):
        m = re.search(r"^Implements: (.*)$", p.read_text(), re.M)
        for rid in ID.findall(m.group(1)) if m else []:
            out.append((rel(root, p), "implements", rid))
    for num, p in adrs.items():
        text = p.read_text()
        m = re.search(r"^- Links: (.*)$", text, re.M)
        decided = ID.findall(m.group(1)) if m else []
        if not m:
            d = re.search(r"## Decision\s*\n(.*?)(\n## |\Z)", text, re.S)
            decided = ID.findall(d.group(1)) if d else []
        out += [(num, "decides", rid) for rid in dict.fromkeys(decided)]
        s = re.search(r"^- Status: Superseded by (\d{4})", text, re.M)
        if s:
            out.append((s.group(1), "supersedes", num))
        out += [(num, "mentions", other) for other in dict.fromkeys(ADR_REF.findall(text)) if other != num]
    for pattern in MENTION_SOURCES:
        for p in sorted(root.glob(pattern)):
            if p.name == "spec.md" or rel(root, p) in NOT_MENTIONS:
                continue
            text, src = p.read_text(errors="replace"), rel(root, p)
            implemented = {d for s, r, d in out if s == src and r == "implements"}
            for rid in dict.fromkeys(ID.findall(text)):
                if rid in ids and rid not in implemented:
                    out.append((src, "mentions", rid))
            for num in dict.fromkeys(ADR_REF.findall(text)):
                out.append((src, "mentions", num))
    return out


def problems(root=None):
    """Broken links: a relation pointing to an id, ADR or file that does not exist."""
    root = root or ROOT
    ids, adrs, out = spec_ids(root), adr_files(root), []
    for src, relation, dst in edges(root):
        if relation == "proved_by":
            continue  # checked by spec_check.py
        if ID.fullmatch(dst) and dst not in ids and relation in ("implements", "decides"):
            out.append(f"{src} {relation} {dst}, which is not in the spec")
        if re.fullmatch(r"\d{4}", dst) and dst not in adrs:
            out.append(f"{src} {relation} ADR {dst}, which does not exist")
    return sorted(set(out))


def orphans(root=None):
    root = root or ROOT
    ids, e = spec_ids(root), edges(root)
    coded = {d for s, r, d in e if r == "implements"}
    tested = {s for s, r, d in e if r == "proved_by"}
    no_code = [i for i in ids if i not in coded and i not in PROCESS_RULES]
    no_test = [i for i in ids if i not in tested]
    return no_code, no_test


def describe(node, adrs):
    if re.fullmatch(r"\d{4}", node) and node in adrs:
        return f"ADR {node} ({adrs[node].stem[5:].replace('-', ' ')})"
    return node


LABELS = {("decides", "in"): "decided by", ("implements", "in"): "enforced in code by",
          ("proved_by", "out"): "proved by", ("mentions", "in"): "mentioned in", ("supersedes", "in"): "superseded by",
          ("supersedes", "out"): "supersedes", ("decides", "out"): "decides", ("implements", "out"): "implements",
          ("mentions", "out"): "mentions", ("proved_by", "in"): "proves"}


def what(node, root=None):
    root = root or ROOT
    node = node.strip().removeprefix("ADR ").strip()
    ids, adrs, e = spec_ids(root), adr_files(root), edges(root)
    if re.fullmatch(r"\d{1,4}", node):
        node = node.zfill(4)
    lines = []
    if node in ids:
        lines.append(f"{node}: {ids[node]}")
    elif node in adrs:
        lines.append(describe(node, adrs))
    groups = {}
    for s, r, d in e:
        if s == node or s.split("#")[0] == node:
            groups.setdefault(LABELS[(r, "out")], []).append(describe(d, adrs))
        if d == node or d.split("#")[0] == node:
            groups.setdefault(LABELS[(r, "in")], []).append(describe(s, adrs))
    for label, items in groups.items():
        lines.append(f"  {label}: " + ", ".join(dict.fromkeys(items)))
    return "\n".join(lines) if len(lines) > (1 if lines and (node in ids or node in adrs) else 0) else f"{node}: no links"


def store(con, root=None):
    """Write the edges into an open index database (called by memory_index.py build)."""
    con.execute("CREATE TABLE edges (src TEXT, rel TEXT, dst TEXT)")
    con.executemany("INSERT INTO edges VALUES (?,?,?)", edges(root))


def obsidian_notes(vault_dir, vault_path_of):
    """One note per requirement in <vault>/requirements/, linking its decisions, code and tests, so the
    graph view shows real clusters (rule, decision, code, test) instead of one star."""
    ids, adrs, e = spec_ids(), adr_files(ROOT), edges()
    folder = vault_dir / "requirements"
    folder.mkdir(exist_ok=True)
    for old in folder.glob("*.md"):  # only notes this script wrote; Ioseb's own notes stay
        if MARK in old.read_text(errors="replace")[:300]:
            old.unlink()

    def wl(repo_path):
        target = vault_path_of(repo_path.split("#")[0])
        return f"[[{target}|{Path(repo_path).name}]]" if target else repo_path

    for rid, title in ids.items():
        rows = [f"# {rid}: {title}", "", f"{MARK} Source: {wl('docs/spec.md')}", ""]
        for label, relation, side in (("Decided by", "decides", "in"), ("Enforced in code by", "implements", "in"),
                                      ("Proved by", "proved_by", "out"), ("Mentioned in", "mentions", "in")):
            items = [s if side == "in" else d for s, r, d in e if r == relation and (d if side == "in" else s) == rid]
            if items:
                rows.append(f"## {label}")
                rows += [f"- {wl(str(adrs[i].relative_to(ROOT)) if i in adrs else i)}" for i in dict.fromkeys(items)]
                rows.append("")
        (folder / f"{rid}.md").write_text("\n".join(rows))
    return sorted(ids, key=lambda x: (x[0], int(x[1:])))


def main():
    cmd, rest = (sys.argv[1] if len(sys.argv) > 1 else "orphans"), sys.argv[2:]
    if cmd == "what" and rest:
        print(what(" ".join(rest)))
    elif cmd == "orphans":
        no_code, no_test = orphans()
        print("No code enforces (chatbot rules only): " + (", ".join(no_code) or "none"))
        print("No test proves: " + (", ".join(no_test) or "none"))
        broken = problems()
        for b in broken:
            print("BROKEN LINK: " + b)
        print("ALL LINKS OK" if not broken else f"{len(broken)} BROKEN LINK(S)")
        sys.exit(1 if broken else 0)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
