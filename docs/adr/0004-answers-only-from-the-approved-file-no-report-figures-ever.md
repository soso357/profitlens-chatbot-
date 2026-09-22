# ADR 0004: Answers only from the approved file; no report figures ever

- Status: Accepted
- Date: 2026-09 (founder brief)
- Decided by: Founders

## Context

Chatbot statements can create legal liability, and website figures have documented defects.

## Decision

The agent answers only from content/approved-answers.md. It never states figures, savings, profit or percentages. Enforced in the prompt and in code (spec G1).

## Consequences

Some visitors will not get an answer and are handed off by email. That is the intended behaviour.
