# ADR 0010: Fully automatic session summaries

- Status: Accepted
- Date: 2026-09-22
- Decided by: Ioseb (chose option: fully automatic)

## Context

Session summaries feed project context and self improvement. Options were a manual /wrap-up skill, automatic with a manual option, or fully automatic.

## Decision

A SessionEnd hook starts a detached background job that condenses the transcript and runs a headless Claude call (claude -p, Sonnet) to write memory/episodic/sessions/<date>-<id>.md and any improvement proposals to memory/proposals/. Sessions with fewer than 3 real user messages are skipped. The job runs from a temporary folder so project hooks do not fire again (no loop).

## Consequences

Costs a small amount of usage per real session. Nobody reviews a summary before it is written, so summaries are marked 'unreviewed' until Ioseb or Claude checks them at the next session start. Secrets are scrubbed before and after the call.
