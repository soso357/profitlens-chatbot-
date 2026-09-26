# ADR 0022: Handoff protocol: one handoff per task, fresh session at 70%

- Status: Accepted
- Date: 2026-09-26
- Decided by: Ioseb (interview answers, recommended options except where noted)

## Context

Ioseb works with several Claude Code terminals at once and has four kinds of sessions: Plan, Build, Fix (live incident), Content and review. The single memory/working/handoff.md is shared by all terminals, so they can overwrite each other. Compaction (a summary of a summary) loses detail each time. Options asked: handoff per task, per session type, or one shared file; compact up to 3 times or hand off at 70%; start sessions with a brief, auto continue, or clean.

## Decision

One handoff file per task or branch, fixed one page template (goal, state, decisions, open questions, next step, do not redo, files). New sessions start clean and load context only when Ioseb says "resume". At 70% context Claude hands off and asks for a new terminal; compaction remains only as a safety net. A new session is also suggested when a task finishes or the session type changes. Fix sessions write an incident note with a required test. When sources disagree, a fixed precedence order applies (founder ADRs, spec, ADRs, plan, progress, lessons, summaries, handoffs). Summary items are sorted automatically into progress.md; plan, spec, ADR and rule changes become proposals. Details: docs/foundation-v2.md section 1.

## Consequences

Parallel terminals stop clashing on the handoff. Less drift, since no session runs on repeated summaries. Ioseb must open new terminals more often and say "resume". Partly replaces ADR 0012 (3 compactions rule) once built.
