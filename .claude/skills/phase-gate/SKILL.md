---
name: phase-gate
description: End-of-phase demonstration checklist for the ProfitLens build (rules R12 and R13). Use when a build phase looks finished, before telling Ioseb it is done, or when he asks to demo a phase.
---

# Phase gate

Do not say a phase is done until every item is true.

1. Re-read the phase's "Demonstrate" line in docs/plan.md. That is the acceptance test.
2. Run it for real (service started, requests sent, emails or calendar checked). Paste the actual output, not a description.
3. At least ten realistic visitor conversations for this phase, including rude, off topic and trick questions (R13); Phase 1 needs 15 in tests/conversations.md. Show the transcripts or the pass/fail table.
4. Check the guardrails relevant to this phase caught real violations (show at least one catch each).
5. Run `grep -rn $'—\|–' content app` and confirm no dashes (R4).
6. Update the status table in docs/plan.md and add a line to docs/build-log.md.
7. Tell Ioseb, in plain English: what works, how you verified it, what you could not do and why, what you need from him or the founders.
8. Stop. Wait for the word "approved". Only then mark the phase approved in docs/plan.md.
