---
title: Edge-case test suite for the session summarizer's skip logic
status: proposed
kind: test
source: 2026-09-23-919cea64.md
created: 2026-09-23
---

## Why
The summarizer's first skip rule would have wrongly skipped a real session (single long user message) and was only caught by manually dry-running it on this session's own transcript.

## What
A small test suite covering summarizer skip-rule edge cases (single message, no assistant reply, very short sessions) so bugs like this are caught automatically instead of by manual spot-check.

## Decision
(pending Ioseb)
