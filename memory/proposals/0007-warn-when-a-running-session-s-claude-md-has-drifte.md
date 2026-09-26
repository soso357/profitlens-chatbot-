---
title: Warn when a running session's CLAUDE.md has drifted from disk
status: rejected
kind: hook
source: 2026-09-23-919cea64.md
created: 2026-09-23
---

## Why
The other terminal kept a stale CLAUDE.md loaded for the whole session and kept violating the new rules (appending decisions to CLAUDE.md, committing all files at once) until manually told to re-read it.

## What
A hook or startup check that records a hash of CLAUDE.md at session start and warns Claude if the on-disk file changes mid-session, prompting a re-read.

## Decision
Ioseb, 2026-09-26 (proposal review): rejected. Claude Code already tells the session when CLAUDE.md changes on disk.
