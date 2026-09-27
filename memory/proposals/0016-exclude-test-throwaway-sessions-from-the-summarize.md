---
title: Exclude test/throwaway sessions from the summarizer
status: rejected
kind: hook
source: 2026-09-26-174858-298f6ef5.md
created: 2026-09-26
---

## Why
Compaction-testing sessions this session were auto-summarized and created a duplicate proposal (0016) that had to be manually found and deleted.

## What
Add a marker or naming convention for test sessions and skip them in the session-summary generator.

## Decision
Ioseb, 2026-09-27 (trim workflow overhead, ADR 0028): rejected. Summarizer tooling, not a Phase 5 launch blocker; workflow tooling is paused.
