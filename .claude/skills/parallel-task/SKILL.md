---
name: parallel-task
description: Set up the git worktree for a task. Every open task in memory/working/handoffs/ has its own worktree (ADR 0028). Use when a new task is opened, when an open task has no worktree yet, when Ioseb wants to work on two things in parallel or opens a second terminal, and to remove a worktree once its pull request is merged (ADR 0023 C2).
---

# Parallel task (ADR 0023 C2)

A git worktree is a second copy of the project folder on its own branch. Two terminals in two worktrees never switch each other's branch or overwrite each other's files. Memory and handoffs stay shared in the main folder (the scripts find it).

Rule (ADR 0028): one worktree per open task. The main folder is only for Maintain work, resume and memory. `git worktree list` should show the main folder plus one worktree per open handoff, and nothing else.

1. Agree the task name and type with Ioseb. If the task already has a branch, use `git worktree add ../PROFITLENS-CHATBOT-wt/<task> <branch>` in step 2 instead. Branch name: `phase-N-name` or `maintain-name`.
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
