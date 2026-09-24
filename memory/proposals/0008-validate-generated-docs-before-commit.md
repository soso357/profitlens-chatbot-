---
title: Validate generated docs before commit
status: proposed
kind: test
source: 2026-09-23-919cea64.md
created: 2026-09-23
---

## Why
ADR 0007 was generated with a double-backslash escaping bug that had to be caught and fixed by hand after the fact.

## What
A lint/test step that checks generated ADRs and other scripted docs for common formatting mistakes (escaping, broken links) before they are committed.

## Decision
(pending Ioseb)
