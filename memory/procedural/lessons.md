---
title: Lessons learned
---

# Lessons learned

When Claude makes the same mistake twice, it goes here: date, what happened, the rule that prevents it. Lessons that keep mattering are proposed as rules (.claude/rules/) or hooks, then removed from this list.

- 2026-09-22: Two Claude Code sessions worked in this repo at the same time and one changed CLAUDE.md while the other was reading it. Rule: before editing a shared file (CLAUDE.md, docs/plan.md, docs/build-log.md), re-read it right before the edit and change only your own lines.
- 2026-09-22: Transcript user messages can start with pasted content tags, so filtering "anything starting with <" dropped real requests. Rule: filter only known harness prefixes (common.NOISE_PREFIXES).
- 2026-09-26: A hook tested only by feeding it fake input can still be rejected by Claude Code itself. The PreCompact hook's output was refused on every compaction for four days and nobody saw it. Test a new or changed hook once in a real session (claude -p, then --resume with /compact) and read the transcript for 'failed'.
