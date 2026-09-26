# ADR 0024: Agent harness: allow, ask, deny lists and a guard hook

- Status: Accepted
- Date: 2026-09-26
- Decided by: Ioseb (approved the foundation v2 step 3 plan note)

## Context

Until now Claude Code had only a deny list. The Read deny rules for .env did not stop a shell command such as "cat .env", nothing stopped writes outside the project, and nothing separated "fine to do" from "ask Ioseb first".

## Decision

Three permission lists in .claude/settings.json: allow (tests, evals, lint, git status, diff, log, add, commit, the project's scripts), ask (push, pull requests, installing libraries, deleting files, the network, content/, CLAUDE.md, settings, git hooks) and deny (merge, push to master, force push, hard reset, skipping hooks, .env and secrets/). A PreToolUse guard hook (.claude/scripts/guard.py) runs before every tool use and refuses what the lists cannot express: shell access to .env, secrets/ or credential files; writes outside the project, its worktrees, the scratchpad and Claude's own memory; commits on master; pushes to master; merges; deleting or editing visitor data; git clean and hard reset. tests/check_harness.py tries each refused action. Sandboxing is left for later because live checks need the network.

## Consequences

Secrets cannot leak through the shell. A command whose text merely mentions .env is refused too, so Claude rewords it. Ioseb gets a prompt for pushes, pull requests, content edits and network calls. The approval points stay: plan notes, spec, pull request merge, founder approval.
