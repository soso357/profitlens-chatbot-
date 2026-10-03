# ADR 0023: Foundation v2 choices C1 to C7

- Status: Accepted, partly superseded by 0030
- Date: 2026-09-26
- Decided by: Ioseb ("all recommended")

## Context

docs/foundation-v2.md listed seven open choices, each with options and a recommendation.

## Decision

C1 the phase status table moves to docs/progress.md. C2 each parallel task gets its own git worktree (a second copy of the project folder on its own branch). C3 the 70% stop is soft: Claude is told to stop, Ioseb can override. C4 context graph option A: typed links in file headers, built into the SQLite index and shown in Obsidian. C5 development tools approved: ruff, pytest, pip-audit, GitHub Actions, a secret scanner. C6 multi model orchestration is design only for now. C7 build in the order of foundation-v2 section 9; Phase 5 launch items continue in parallel sessions.

## Consequences

Seven build steps, each a pull request. The new tools are for development only and never run in the live service.
