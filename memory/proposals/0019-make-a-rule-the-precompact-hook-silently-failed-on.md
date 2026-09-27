---
title: Make a rule: The PreCompact hook silently failed on every prior compaction; only a 
status: deferred
kind: rule
source: 2026-09-26-174858-298f6ef5.md
created: 2026-09-26
---

## Why
The same lesson came up again in 2026-09-26-174858-298f6ef5.md: The PreCompact hook silently failed on every prior compaction; only a real end-to-end compaction test revealed and confirmed the fix

## What
A rule in .claude/rules/ or CLAUDE.md, or a hook, so it cannot happen a third time.

## Decision
Ioseb, 2026-09-27 (trim workflow overhead, ADR 0028): deferred. PreCompact is fixed and compaction is only a safety net; revisit only if it fails again.
