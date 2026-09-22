---
title: Skill to run the scripted visitor conversations and check the guardrails
status: proposed
kind: skill
source: 2026-09-22 workflow setup session
created: 2026-09-22
---

## Why
Rule R13 requires at least ten realistic visitor conversations per phase, and Phase 1 requires 15 scripted ones. That is the same manual job repeated in every phase (1 to 5). The playbook also says every production incident should become a permanent regression case.

## What
A project skill `run-visitor-evals` plus a small script: reads the scripted conversations in tests/, sends them to the local service, saves transcripts, and checks each reply automatically against R1 to R6 and G1 to G3 (no figures, disclosure first, no dashes, length, one question). Prints a pass/fail table for the phase demo. Built with skill-creator in Phase 1.

## Decision
(pending Ioseb)
