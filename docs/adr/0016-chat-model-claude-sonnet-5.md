# ADR 0016: Chat model is Claude Sonnet 5

- Status: Accepted (supersedes ADR 0013; ADR 0017 uses Haiku during testing)
- Date: 2026-09-24
- Decided by: Ioseb (chose Sonnet after a side by side test)

## Context

ADR 0013 chose Claude Haiku 4.5 and said to revisit if Haiku slipped in testing. In the Phase 1 run with the real API key, the same 17 scripted conversations were run on both models after the fixes. Both passed every safety rule, length and "no selling" check. When a visitor gave several answers in one message (conversation 16), Sonnet understood them and offered call times; Haiku asked another question.
Prices per million tokens: Sonnet 5 $2 in, $10 out; Haiku 4.5 $1 in, $5 out. Estimated cost per conversation: about $0.05 versus $0.03.

## Decision

Use Claude Sonnet 5 (claude-sonnet-5) for the website chat. The code keeps a price table per model so the daily spend cap stays correct if the model changes.

## Consequences

About $0.02 more per conversation (about $2 more per 100 conversations). Booking, the step that brings customers, is handled more reliably. Switching back is one setting: CLAUDE_MODEL=claude-haiku-4-5.
