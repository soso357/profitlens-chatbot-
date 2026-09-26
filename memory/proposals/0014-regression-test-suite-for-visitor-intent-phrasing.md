---
title: Regression test suite for visitor intent phrasing
status: approved
kind: test
source: 2026-09-26-919cea64.md
created: 2026-09-26
---

## Why
Common buying phrases ('I want to use...', 'sign me up') were missed by the intent filter and had to be fixed in two passes, the first fix over-matching unrelated questions; similar ambiguity showed up with 'LA' as a location.

## What
A small fixture file of real visitor phrasings (buying intent, location ambiguity, email typos) run against the guardrails on every content or prompt change, so future edits don't silently break intent recognition.

## Decision
Ioseb, 2026-09-26 (proposal review): approved. Real visitor phrasings become a fixture run by tests/evals.py.
