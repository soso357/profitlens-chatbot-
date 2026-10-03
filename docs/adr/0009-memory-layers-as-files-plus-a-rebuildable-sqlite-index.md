# ADR 0009: Memory layers as files plus a rebuildable SQLite index

- Status: Accepted, partly superseded by 0030
- Date: 2026-09-22
- Decided by: Ioseb (chose option: Markdown plus SQLite index)

## Context

The agent needs to carry knowledge across sessions: the current task (working), facts about the project (semantic), how to do things (procedural), and what happened before (episodic). Options were SQLite only, Markdown only, or Markdown plus an index.

## Decision

Every memory is a Markdown file in git (memory/, .claude/rules/, .claude/skills/, docs/). memory/index.sqlite is a search index rebuilt from those files by .claude/scripts/memory_index.py. It is git ignored and can be deleted at any time.

## Consequences

Humans can read and review every memory in git. Search is fast. The index can never be the only copy of anything.
