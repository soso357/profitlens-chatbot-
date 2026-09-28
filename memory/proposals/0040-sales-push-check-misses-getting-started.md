---
title: Sales push check misses "or would you like help getting started?"
status: built
kind: test
source: live eval chat #18, 2026-09-28 (branch build-p5-simplify-qualifying, PR #14)
created: 2026-09-28
---

## Why
Evidence: in live chat #18 the visitor said "Ok thanks" and the agent replied "Anything else you would like to know about ProfitLens, or would you like help getting started?". Prompt rule 15 forbids this, and guardrails.remove_sales_push should drop it, but its word list has "get started" and "start", not "getting started" or "help". Cost if ignored: a mild but repeated sales nudge on real visitors, against the "never sells" intent.

## What
Widen `_PUSH` and the trailing "or would you like ..." cleanup in app/guardrails.py to cover "getting started", "help (you )?get(ting)? started" and similar. Add the chat #18 reply as a case in tests/check_guardrails.py (expect the tail removed, neutral question kept).

## Decision
2026-09-28: approved by Ioseb ("fix it"). Built: app/guardrails.py remove_sales_push, tests/check_guardrails.py (PR #15, merged).
