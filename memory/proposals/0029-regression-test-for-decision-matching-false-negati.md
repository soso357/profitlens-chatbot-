---
title: Regression test for decision-matching false negatives
status: rejected
kind: test
source: 2026-09-27-170037-2f71faae.md
created: 2026-09-27
---

## Why
The stricter stem-based matching added this session was later found by code review to hide a real decision ('kill switch: build it now' matched 'kill switch postponed') before being fixed with topic-and-choice matching.

## What
Add a fixed set of real historical decision pairs that must never match, and run it automatically whenever the matching logic changes.

## Decision
Ioseb, 2026-09-27 (trim workflow overhead, ADR 0028): rejected. Summarizer matching tooling, not a launch blocker; workflow tooling is paused.
