---
title: Pre-write staleness check
status: rejected
kind: hook
source: 2026-09-22-919cea64.md
created: 2026-09-22
---

## Why
This session had to repeatedly and manually re-read CLAUDE.md and settings.json right before writing to avoid clobbering concurrent edits from the other terminal session working on the same repo.

## What
A hook that compares a file's mtime or hash at write time against what was last read, and warns before overwriting if the file changed in between.

## Decision
Ioseb, 2026-09-26 (proposal review): rejected. Claude Code already refuses or warns when a file changed since it was read.
