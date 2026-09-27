---
title: Guardrail against deleting Ioseb's own Obsidian notes
status: rejected
kind: test
source: 2026-09-27-170037-2f71faae.md
created: 2026-09-27
---

## Why
Code review found the graph sync could delete notes Ioseb writes himself in Obsidian's requirements folder; it was fixed reactively rather than caught by an existing check.

## What
Add a test that fails if the graph sync script would delete any file not marked as auto-generated.

## Decision
Ioseb, 2026-09-27 (trim workflow overhead, ADR 0028): rejected. Obsidian map rebuild is switched off by default (ADR 0028), so the sync no longer runs.
