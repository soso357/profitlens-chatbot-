---
name: handoff
description: Write or update memory/working/handoff.md so work can continue after compaction or in a new session. Use when context reaches 60% (a hook will say so), before a break, before /clear, or when the user says handoff, pause, or "continue in a new window".
---

# Handoff

Write memory/working/handoff.md (replace the old content). Under 60 lines. Plain English. No secrets.

```
# Handoff (YYYY-MM-DD HH:MM, session <first 8 chars of id if known>)

## Goal
What the user is trying to achieve in this session, in their words.

## Current state
Phase and gate status. What works right now, verified how.

## Decisions made this session
- decision, option chosen, by whom (and ADR number if written)

## Files touched
- path: what changed

## Waiting on the user
- questions asked and not answered yet

## Next step
The single exact next action, then the one after.

## Do not redo
Research or work already saved elsewhere (link paths instead of repeating content).
```

Then:
1. If a decision was made and has no ADR yet, write it (skill: new-adr) and add a line to docs/build-log.md.
2. If the user is leaving this terminal, tell them: open a new terminal in this folder, start `claude`, and say "continue from the handoff". The session start hook will point the new session to it.

Do not duplicate content from docs/ or memory/semantic/. Reference paths.
