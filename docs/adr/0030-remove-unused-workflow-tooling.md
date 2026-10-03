# ADR 0030: Remove unused workflow tooling

- Status: Accepted
- Date: 2026-10-03
- Decided by: Ioseb (option 1, delete everything unused)
- Links: none (workflow only, no chatbot behaviour changes)
- Supersedes: 0010; parts of 0009 (search index), 0023 C4 (context graph) and 0028 items 2 and 3

## Context

A structure review against Anthropic's Claude Code guidance (start simple, keep memory curated, add tooling only when it clearly helps) found the workflow tooling was larger than the chatbot: about 2,900 lines of scripts and their tests against about 2,000 lines of app code. Since 2026-09-26, 39 of 72 commits were about the workflow. ADR 0028 had switched some of it off but kept the code.

Unused or low value:
- Session summarizer (session_end.py, summarize_session.py, distribute.py, memory/episodic/): a headless Claude call after each session wrote unreviewed lines into progress.md and lessons.md, often duplicates, and filed many "record decision" proposals. Handoffs, progress.md and git history already cover continuity.
- Search index (memory_index.py, memory/index.sqlite, recall skill): a database over about 150 text files that Claude can grep directly.
- Context graph (graph.py, obsidian_map.py, tests/check_graph.py): already off since ADR 0028.
- 30 rejected or built proposals, a stale test transcript from an old model, and the finished foundation v2 design document.

Options offered:
1. Delete all of the above. Pros: least upkeep, simplest setup. Cons: losing automatic summaries; old files only in git history.
2. Delete the dead code, switch the summarizer and index off but keep their files. Pros: easy to undo. Cons: dead code stays.
3. Wait until after the launch. Pros: no risk now. Cons: overhead continues.

## Decision

Option 1. The files above are deleted (closed proposals remain in git history), the SessionEnd hook is removed, docs/foundation-v2.md moves to docs/archive/. The chatbot code (app/), content/, the guardrails, the evals, CI checks, git hooks, permissions, handoffs and the propose-capability skill stay.

## Consequences

Faster session starts, fewer hooks, less to maintain, no more automatic duplicate lines or proposals. Claude now updates progress.md and lessons.md by hand in each task handoff. Old summaries and closed proposals are found with `git log`. Verified before merging: app/ referenced none of the removed files and the offline evals passed before and after.
