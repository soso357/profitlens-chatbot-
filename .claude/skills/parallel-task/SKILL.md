---
name: parallel-task
description: Set up a separate git worktree for a task that runs in a second terminal at the same time as another one. Use when Ioseb wants to work on two things in parallel, opens a second terminal for a different task, or asks for a new parallel session (ADR 0023 C2).
---

# Parallel task (ADR 0023 C2)

A git worktree is a second copy of the project folder on its own branch. Two terminals in two worktrees never switch each other's branch or overwrite each other's files. Memory and handoffs stay shared in the main folder (the scripts find it).

1. Agree the task name and type with Ioseb. Branch name: `phase-N-name` or `maintain-name`.
2. From the main folder:
   ```
   git fetch origin
   git worktree add ../PROFITLENS-CHATBOT-wt/<task> -b <branch> origin/master
   ln -s "$PWD/.venv" ../PROFITLENS-CHATBOT-wt/<task>/.venv
   ```
   (The .venv link reuses the installed libraries. .env and secrets/ are deliberately not copied: anything that talks to the live site, Telegram, Gmail or the Anthropic API runs in the main folder only. Offline evals work in the worktree.)
3. Write the task's first handoff (skill: handoff) with `worktree:` set to that folder, status open, and the goal.
4. Tell Ioseb:
   ```
   Open a new terminal, then:
   cd ~/Desktop/PROFITLENS-CHATBOT-wt/<task> && claude
   and say: resume
   ```
5. When the task's pull request is merged: `git worktree remove ../PROFITLENS-CHATBOT-wt/<task>` from the main folder (ask Ioseb first; it refuses if there are uncommitted changes, which is correct).
