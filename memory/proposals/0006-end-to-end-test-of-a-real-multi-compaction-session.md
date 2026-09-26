---
title: End-to-end test of a real multi-compaction session
status: built
kind: test
source: 2026-09-22-919cea64.md
created: 2026-09-22
---

## Why
The context guard, compaction counter, and STOP indicator were only verified with mock data and simulated compactions, not an actual long session.

## What
A real or scripted long session that runs through 3-4 genuine compactions to confirm the statusline warning and handoff instructions behave as designed in practice.

## Decision
Built 2026-09-26: a real headless session was compacted 3 times. Counter, LIMIT REACHED and SESSION LIMIT messages all fired. It also found that Claude Code rejected the PreCompact hook's output on every compaction; fixed (instructions moved to CLAUDE.md "Compact instructions", hook now silent) and rechecked on a real compaction.
