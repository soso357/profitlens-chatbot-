---
title: End-to-end test of a real multi-compaction session
status: proposed
kind: test
source: 2026-09-22-919cea64.md
created: 2026-09-22
---

## Why
The context guard, compaction counter, and STOP indicator were only verified with mock data and simulated compactions, not an actual long session.

## What
A real or scripted long session that runs through 3-4 genuine compactions to confirm the statusline warning and handoff instructions behave as designed in practice.

## Decision
(pending Ioseb)
