---
name: handoff
description: Write or update this task's handoff in memory/working/handoffs/ so work can continue in a new session. Use when context reaches 60% or 70% (a hook will say so), when a task is finished, when the session type changes, before a break or /clear, or when the user says handoff, pause, or "continue in a new window".
---

# Handoff (ADR 0022)

One handoff per task or branch. Several terminals may be open, so write only your own task's file.

1. Find the path (works from a worktree too): `python3 .claude/scripts/handoffs.py path <task name>`. Reuse the existing slug if this task already has a handoff (`python3 .claude/scripts/handoffs.py list`).
2. Write it with the Write tool (replace the old content), exactly this template, one page, plain English, no secrets, no visitor data:

```
---
task: <slug>
type: Plan | Build | Fix | Content
branch: <git branch>
worktree: <folder, if not the main project folder>
commit: <output of git rev-parse --short HEAD>
updated: YYYY-MM-DD HH:MM
status: open | done
---

## Goal
One or two lines, in Ioseb's words.

## State
What works now and how it was verified. What is half done.

## Decisions
- decision, option chosen, by whom, ADR number

## Open questions
- question (who must answer: Ioseb or a founder)

## Next step
The single next action, then the one after.

## Do not redo
- what failed and why; research already saved elsewhere (paths only)

## Files
- path: what changed (mark uncommitted ones with *)
```

Not carried forward: tool output, file contents, dead ends without a lesson, anything already in docs/ (link it).

3. Then:
   - Every decision without an ADR: write it (skill: new-adr) and a line in docs/build-log.md.
   - Open questions and people we wait on also go in docs/progress.md (one home for them).
   - Task finished: set `status: done`, move the result to the "Done" list in docs/progress.md.
   - Fix session: also write the incident note (memory/incidents/README.md has the template). The "Test added" line is required; the lesson goes to memory/procedural/lessons.md.
4. If the session should end (70%, task done, type changed), tell Ioseb in two lines: open a new terminal in this folder, start `claude`, say resume.
