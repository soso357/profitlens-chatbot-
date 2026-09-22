# ADR 0001: Custom build with Claude Code, not an off the shelf chat tool

- Status: Accepted
- Date: 2026-09 (founder brief)
- Decided by: Founders

## Context

Off the shelf chat tools make it hard to guarantee answers come only from an approved file and to enforce figure and promise blocks in code.

## Decision

Build a custom FastAPI chat service with Claude Code.

## Consequences

Full control over guardrails. We own maintenance; the README must let founders edit answers without a developer.
