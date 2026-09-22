# ADR 0008: AI native SDLC artifact chain for development

- Status: Accepted
- Date: 2026-09-22
- Decided by: Ioseb

## Context

One 160 line CLAUDE.md mixed the brief, rules, phase plan and a growing build log. Claude reads CLAUDE.md in full every session, so stale or bulky content costs context and attention. Anthropic's AI native SDLC playbook recommends a chain of versioned artifacts where each stage commits a file the next stage reads.

## Decision

Split into docs/intent.md (what and why), docs/spec.md (numbered requirements), docs/plan.md (phases and status), docs/adr/ (decisions), docs/build-log.md (events), REVIEW.md (review policy). CLAUDE.md stays under one page and points to them. The founders' original brief stays unchanged at the repo root as the historical source.

## Consequences

Claude reads only the artifact a task needs. Every requirement has an id that code and tests can cite. Two sessions editing at once must now coordinate on which file they touch.
