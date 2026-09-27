#!/usr/bin/env python3
"""Rebuild the Obsidian map note (START HERE) so every project note and code file
is linked and nothing shows as unconnected in Obsidian's graph.

The vault folder holds live links (symlinks) into this project; see
memory/semantic/project-facts.md. Does nothing if the vault folder is missing.
Run by session_start.py; safe to run by hand.
"""
import os
from pathlib import Path

VAULT_DIR = Path.home() / "Desktop" / "IOSEB" / "IOSEB" / "PROFITLENS CHATBOT"
BASE = "PROFITLENS CHATBOT"
SKIP_DIRS = {"__pycache__", "working", ".git"}
SKIP_FILES = {"START HERE.md", "index.sqlite", ".gitkeep", ".DS_Store"}

SECTIONS = [
    ("The build", ["docs/intent.md", "docs/spec.md", "docs/plan.md", "docs/build-log.md", "docs/workflow.md", "Original founders brief.md"]),
    ("Decisions (ADRs)", ["docs/adr"]),
    ("Research", ["docs/research"]),
    ("Other docs and screenshots", ["docs"]),
    ("What the chatbot knows (founders own this)", ["chatbot content"]),
    ("Memory", ["memory/README.md", "memory/semantic", "memory/procedural"]),
    ("Improvement proposals", ["memory/proposals"]),
    ("Session summaries", ["memory/episodic/sessions"]),
    ("Instructions for Claude", ["CLAUDE.md", "REVIEW.md", "claude rules", "claude skills"]),
    ("Code", ["code"]),
]


def files_under(rel):
    p = VAULT_DIR / rel
    if p.is_file():
        return [rel]
    out = []
    for root, dirs, files in os.walk(p, followlinks=True):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if f not in SKIP_FILES and not f.endswith((".pyc", ".tmp")):
                out.append(str(Path(root, f).relative_to(VAULT_DIR)))
    return out


def link(rel):
    target = rel[:-3] if rel.endswith(".md") else rel
    label = Path(rel).stem if rel.endswith(".md") else Path(rel).name
    parent = Path(rel).parent.name
    if label in ("README", "SKILL") and parent:
        label = f"{parent} ({label})"
    return f"- [[{BASE}/{target}|{label}]]"


def vault_path_of(repo_rel):
    """The vault path (without .md) of a project file, found through the vault's live links."""
    target = (Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2]) / repo_rel).resolve()
    for root, dirs, files in os.walk(VAULT_DIR, followlinks=False):
        for name in dirs + files:
            p = Path(root, name)
            if p.is_symlink():
                real = p.resolve()
                if real == target or real in target.parents:
                    inner = target.relative_to(real) if real != target else Path()
                    found = (p.relative_to(VAULT_DIR) / inner) if str(inner) != "." else p.relative_to(VAULT_DIR)
                    s = str(found)
                    return f"{BASE}/{s[:-3] if s.endswith('.md') else s}"
    return None


def main():
    if not VAULT_DIR.is_dir():
        return
    lines = [
        "# ProfitLens chatbot: start here",
        "",
        "Live view of ~/Desktop/PROFITLENS-CHATBOT. These notes ARE the project files: editing them edits the project.",
        "Edit only the chatbot content freely; ask Claude before changing anything else.",
        "This map is rebuilt automatically at every Claude session start (.claude/scripts/obsidian_map.py). Do not edit it by hand.",
        "Kept out on purpose: .env and secrets (keys, passwords), logs and data (visitor conversations, rule R9).",
    ]
    try:  # one note per requirement, linking its decisions, code and tests (graph.py, step 6)
        from graph import obsidian_notes
        req = obsidian_notes(VAULT_DIR, vault_path_of)
        lines += ["", "## Requirements (context graph: each links its decision, code and tests)"] + [
            f"- [[{BASE}/requirements/{r}|{r}]]" for r in req]
    except Exception as e:
        lines += ["", f"(requirement notes not built: {e!r})"]
    seen = set()
    for title, parts in SECTIONS:
        items = [f for part in parts for f in files_under(part) if f not in seen]
        if not items:
            continue
        seen.update(items)
        lines += ["", f"## {title}"] + [link(f) for f in items]
    tmp = VAULT_DIR / "START HERE.md.tmp"
    tmp.write_text("\n".join(lines) + "\n")
    tmp.replace(VAULT_DIR / "START HERE.md")
    print(f"linked {len(seen)} files")


if __name__ == "__main__":
    main()
