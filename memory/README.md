# Memory architecture

How Claude Code remembers this project between sessions (ADR 0009). Every memory is a readable file in git, except the working folder.

| Layer | Answers the question | Where | Written by | Loaded |
|---|---|---|---|---|
| Working | What am I doing right now? | memory/working/handoffs/<task>.md, one per task (plus snapshots/, state/) | Claude, at 60% and 70% context, when a task ends or the type changes (skill: handoff); hooks write snapshots and state | On resume (skill: resume); this session's own task reinjected after compaction. Git ignored. Always in the main folder, also from a worktree. |
| Project | Where are we now? | docs/progress.md | Claude, at the end of every task and in every handoff | On resume |
| Incidents | What broke live? | memory/incidents/ | Fix sessions (template in its README), with a required test | On demand |
| Semantic | What is true about this project? | memory/semantic/*.md, docs/intent.md, docs/spec.md, content/ | Claude, when a fact is confirmed by Ioseb or a founder | On demand (CLAUDE.md points to them) |
| Procedural | How do we do things here? | CLAUDE.md, .claude/rules/, .claude/skills/, memory/procedural/lessons.md | Claude proposes, Ioseb approves | CLAUDE.md and rules always; skills when triggered |
| Decisions | Why is it like this? | docs/adr/, docs/build-log.md | Claude, whenever Ioseb chooses an option | On demand |
| Prospective | What could be better? | memory/proposals/ (open ones only; closed ones are in git history) | Claude (skill: propose-capability) | Open ones listed at session start and in the statusline |
| Personal | How does Ioseb like to work? | Claude's auto memory (~/.claude/projects/...) | Claude Code itself | Automatically |

## Rules

1. One fact lives in one place. Other places link to it.
2. A memory that turns out wrong is corrected or deleted, not left beside the right one.
   Staleness: files in memory/semantic/ carry `last_verified: date`; after 60 days the resume brief flags them. Deferred proposals come back after 30 days. Handoffs marked done are deleted after 14 days.
3. When two sources disagree the higher one wins and the lower one is fixed: founder ADRs 0001 to 0006, spec.md, other ADRs, plan.md, progress.md, lessons, handoffs (ADR 0022).
4. Lessons: when Claude makes the same mistake twice, it adds a line to memory/procedural/lessons.md, then proposes a rule (kind: rule) so it becomes permanent.
5. Nothing about website visitors (names, emails, transcripts) ever goes in this folder. That data lives only on the server (spec section 5).

## Searching

Use grep over memory/, docs/ and content/. Removed in ADR 0030: the session summarizer, the search index and the context graph.
