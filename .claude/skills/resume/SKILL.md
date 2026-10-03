---
name: resume
description: Load project context and continue a task. Use when Ioseb says resume, continue, "where were we", or "continue from the handoff". New sessions load nothing until then (ADR 0022).
---

# Resume (ADR 0022)

1. Run `python3 .claude/scripts/handoffs.py brief`. It lists open tasks, the phase status and open proposals.
2. Show Ioseb the numbered open tasks (task, type, branch, age) and ask which one. If he already named it, skip the question. If there is none, ask what the new task is and its type (Plan, Build, Fix, Content).
3. For the chosen task, read in this order and nothing more:
   - its handoff (`python3 .claude/scripts/handoffs.py path <task>`)
   - docs/progress.md
   - the files the handoff names under Files and Next step
4. Check for drift: `git log --oneline <commit from the handoff>..HEAD` and `git status --short`. Other terminals may have committed since. If a worktree is named, work there (tell Ioseb to open the terminal in that folder if this is not it).
5. If sources disagree, use the higher one and flag the lower one to be fixed: founder ADRs 0001 to 0006, spec.md, other ADRs, plan.md, progress.md, lessons, handoffs.
6. Before changing anything that has a spec id or an ADR, grep for that id to see what else depends on it.
7. Tell Ioseb in three lines: where the task is, what changed since, the next step. Then continue.
8. Mention "proposed" proposals once at a natural pause.
9. Tidy docs/progress.md: remove open questions that are answered and people no longer waited on, drop Done items older than 30 days, merge duplicates. Commit it on the branch with the next commit.
10. If the brief lists memory to re-check or deferred proposals that are due, ask Ioseb about them once, briefly, at a natural pause.

One session, one task, one type. If the work turns into another type, write the handoff and suggest a new terminal.
