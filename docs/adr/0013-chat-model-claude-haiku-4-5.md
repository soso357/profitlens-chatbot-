# ADR 0013: Chat model is Claude Haiku 4.5

- Status: Superseded by 0016
- Date: 2026-09-22
- Decided by: Ioseb (chose Haiku over the recommended Sonnet 5)

## Context

Phase 1 step 2: choose a cost efficient current model. Options presented: Claude Haiku 4.5, about $0.03 per conversation, cheaper and faster; Claude Sonnet 5, about $0.05 per conversation, recommended for stricter rule following.

## Decision

Use Claude Haiku 4.5 (claude-haiku-4-5) for the website chat.

## Consequences

Lower running cost. Rule following must be proven by the scripted conversations and the code guardrails (spec section 4). If Haiku lets rule breaks through in testing, revisit with a superseding ADR for Sonnet 5.
