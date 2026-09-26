---
title: Fail loudly on no-op scripted edits
status: built
kind: rule
source: 2026-09-22-919cea64.md
created: 2026-09-22
---

## Why
A scripted text replacement in the phase-gate skill silently did nothing (the grep found no match) and the gap was only caught by manual inspection.

## What
A rule that automated edit/replace scripts must verify the target text was found and changed, and raise an error if not.

## Decision
Ioseb, 2026-09-26 (proposal review): approved as a rule; built as a line in memory/procedural/lessons.md.
