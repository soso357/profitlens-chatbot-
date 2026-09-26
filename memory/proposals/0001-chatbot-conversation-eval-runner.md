---
title: Skill to run the scripted visitor conversations and check the guardrails
status: built
kind: skill
source: 2026-09-22 workflow setup session
created: 2026-09-22
---

## Why
Rule R13 requires at least ten realistic visitor conversations per phase, and Phase 1 requires 15 scripted ones. That is the same manual job repeated in every phase (1 to 5). The playbook also says every production incident should become a permanent regression case.

## What
A project skill `run-visitor-evals` that wraps the Phase 1 scripts (tests/run_conversations.py, tests/check_guardrails.py): starts the local service, runs every scripted conversation, checks each reply automatically against R1 to R6 and G1 to G3 (no figures, disclosure first, no dashes, length, one question), and prints a pass/fail table for the phase gate. Each later phase adds its own conversations; each bad live transcript becomes a new case. Built with skill-creator.

## Decision
Built 2026-09-26 as one command instead of a skill (Ioseb approved the audit fixes): tests/evals.py runs all offline checks and every scripted conversation with a verdict from Must, Must not and Ends in lines in tests/conversations.md, and writes tests/eval-report.md. The phase-gate skill runs it before every pull request (ADR 0020). First run: 17 of 17.
