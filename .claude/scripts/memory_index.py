#!/usr/bin/env python3
"""Memory index (ADR 0009). The Markdown files are the truth; this SQLite file
is a disposable search index over them.

  memory_index.py build [--quiet]     rebuild memory/index.sqlite
  memory_index.py search <words>      full text search across all memory
  memory_index.py recent [n]          latest session summaries
  memory_index.py proposals [status]  improvement proposals (default: open)
"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import MEMORY, ROOT, frontmatter  # noqa: E402

DB = MEMORY / "index.sqlite"
SOURCES = [
    ("session", "memory/episodic/sessions/*.md"),
    ("proposal", "memory/proposals/[0-9]*.md"),
    ("semantic", "memory/semantic/*.md"),
    ("lesson", "memory/procedural/*.md"),
    ("adr", "docs/adr/[0-9]*.md"),
    ("doc", "docs/*.md"),
    ("rule", ".claude/rules/*.md"),
    ("skill", ".claude/skills/*/SKILL.md"),
    ("content", "content/*.md"),
]


def build(quiet=False):
    DB.parent.mkdir(parents=True, exist_ok=True)
    tmp = DB.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.execute("CREATE TABLE docs (kind TEXT, path TEXT, title TEXT, status TEXT, date TEXT, body TEXT)")
    con.execute("CREATE VIRTUAL TABLE fts USING fts5(kind, path, title, body)")
    n = 0
    for kind, pattern in SOURCES:
        for p in sorted(ROOT.glob(pattern)):
            meta, body = frontmatter(p)
            title = meta.get("title") or next((l.lstrip("# ").strip() for l in body.splitlines() if l.startswith("#")), p.stem)
            rel = str(p.relative_to(ROOT))
            date = meta.get("ended") or meta.get("created") or p.name[:10]
            con.execute("INSERT INTO docs VALUES (?,?,?,?,?,?)", (kind, rel, title, meta.get("status", ""), date, body))
            con.execute("INSERT INTO fts VALUES (?,?,?,?)", (kind, rel, title, body))
            n += 1
    con.commit()
    con.close()
    tmp.replace(DB)
    if not quiet:
        print(f"indexed {n} files into {DB.relative_to(ROOT)}")


def query(sql, args=()):
    if not DB.exists():
        build(quiet=True)
    con = sqlite3.connect(DB)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def main():
    cmd, rest = (sys.argv[1] if len(sys.argv) > 1 else "search"), sys.argv[2:]
    if cmd == "build":
        build("--quiet" in rest)
    elif cmd == "search":
        q = " ".join(f'"{w}"' for w in " ".join(rest).replace('"', "").split())
        if not q:
            sys.exit("usage: memory_index.py search <words>")
        for kind, path, title, snip in query(
                "SELECT kind, path, title, snippet(fts, 3, '[', ']', ' ... ', 12) FROM fts WHERE fts MATCH ? "
                "ORDER BY rank LIMIT 10", (q,)):
            print(f"{kind:8} {path}\n         {title}\n         {snip}\n")
    elif cmd == "recent":
        n = int(rest[0]) if rest else 5
        for path, title, date in query("SELECT path, title, date FROM docs WHERE kind='session' ORDER BY date DESC LIMIT ?", (n,)):
            print(f"{date}  {path}\n            {title}")
    elif cmd == "proposals":
        statuses = rest or ["proposed", "approved"]
        marks = ",".join("?" * len(statuses))
        for path, title, status in query(f"SELECT path, title, status FROM docs WHERE kind='proposal' AND status IN ({marks}) ORDER BY path", statuses):
            print(f"[{status}] {path}\n           {title}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
