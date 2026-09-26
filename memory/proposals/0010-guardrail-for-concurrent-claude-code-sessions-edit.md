---
title: Guardrail for concurrent Claude Code sessions editing the same repo
status: rejected
kind: hook
source: 2026-09-23-919cea64.md
created: 2026-09-23
---

## Why
The other terminal kept following a stale CLAUDE.md it read at its own session start, causing it to write decisions into the wrong place and commit everything at once instead of by name, until manually corrected this session.

## What
A session-start check that compares CLAUDE.md's content or hash against what was last seen, and warns the new session if it differs from what a concurrently running session might have, or flags commits that were not staged by name.

## Decision
Ioseb, 2026-09-26 (proposal review): rejected. Covered by the pull request flow (ADR 0020) and Claude Code's own changed file notices. Same idea as 0009 and 0011.
