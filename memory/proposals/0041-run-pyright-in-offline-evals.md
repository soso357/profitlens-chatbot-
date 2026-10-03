---
title: Run the type check (pyright) inside the offline evals
status: proposed
kind: test
source: PR #17, 2026-09-29
created: 2026-09-29
---

## Why
Evidence: PR #17 passed every offline eval locally, then failed on GitHub because only GitHub runs pyright (a type error in app/chat_booking.py). Ioseb saw a red "failed" and had to report it. Costs a round trip every time.

## What
Add `.venv/bin/pyright` as one step of `python -m tests.evals --offline` (tests/evals.py), so the local run matches the GitHub check. Test: a deliberate type error makes the offline evals fail.

## Decision
(pending Ioseb)
