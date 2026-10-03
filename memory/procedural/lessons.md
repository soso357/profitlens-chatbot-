---
title: Lessons learned
---

# Lessons learned

When Claude makes the same mistake twice, it goes here: date, what happened, the rule that prevents it. Lessons that keep mattering are proposed as rules (.claude/rules/) or hooks, then removed from this list.

- 2026-09-22: Two Claude Code sessions worked in this repo at the same time and one changed CLAUDE.md while the other was reading it. Rule: before editing a shared file (CLAUDE.md, docs/plan.md, docs/build-log.md), re-read it right before the edit and change only your own lines.
- 2026-09-22: Transcript user messages can start with pasted content tags, so filtering "anything starting with <" dropped real requests. Rule: filter only known harness prefixes (common.NOISE_PREFIXES).
- 2026-09-26: A hook tested only by feeding it fake input can still be rejected by Claude Code itself. The PreCompact hook's output was refused on every compaction for four days and nobody saw it. Test a new or changed hook once in a real session (claude -p, then --resume with /compact) and read the transcript for 'failed'.
- 2026-09-26 (proposal 0005): A scripted edit (sed, a Python replace) must check that the old text was found and fail loudly if not; a silent no-op edit looks like success.
- 2026-09-26: Throwaway test sessions get auto-summarized and can pollute the real proposal list; they need to be excluded (from 2026-09-26-174858-298f6ef5.md)
- 2026-09-26: Non-technical users can be confused by usage instructions for features that don't exist yet; always state clearly that something is unbuilt before describing how to use it (from 2026-09-26-174858-298f6ef5.md)
- 2026-09-26: Summarizer sometimes left the frontmatter header unclosed, making summaries always show as unreviewed; the script now closes the header itself. (from 2026-09-26-174904-2f71faae.md)
- 2026-09-26: Code review before each pull request caught real bugs missed by offline tests at every step; keep running it before every merge. (from 2026-09-26-174904-2f71faae.md)
- 2026-09-26: A one-off unreproducible test slowdown should be treated as noise, not chased further. (from 2026-09-26-174904-2f71faae.md)
- 2026-09-27: The automatic session summarizer's first real run produced mostly duplicate content (12 of 13 progress lines, 7 of 13 proposals already recorded) (from 2026-09-27-170037-2f71faae.md)
- 2026-09-27: A tightened duplicate-matching rule can become too loose and hide a real decision as already recorded; changes to this logic need testing against real cases before shipping, not just after a review catches it (from 2026-09-27-170037-2f71faae.md)
- 2026-09-27: Deleting a whole folder in the Obsidian vault (instead of one note) removes shortcuts to every linked project file; only delete single notes (from 2026-09-27-170044-d2856c37.md)
- 2026-09-27: A Render deploy-failed email for a docs-only commit is a false alarm since the live app code hasn't changed; verify changed files before treating it as urgent (from 2026-09-27-170044-d2856c37.md)
- 2026-09-27: Branch counts should be double-checked before reporting to the user; Claude initially miscounted 14 vs the correct 13, caught before deletion (from 2026-09-27-175421-dccb5168.md)
- 2026-09-27: zsh may not split a list of branch names as expected in a single command; passing names individually is more reliable (from 2026-09-27-175421-dccb5168.md)
- 2026-09-29: Local offline checks did not include pyright, so a type error only showed up on GitHub; run pyright before opening a pull request (from 2026-09-29-103011-0ec43a04.md)
- 2026-09-29: Both the live chats and the terminal live_chat tool use the paid API key; say so before running them (from 2026-09-29-103011-0ec43a04.md)
- 2026-09-29: Check which branch the main folder is on before telling Ioseb to test there, since it may hold old code (from 2026-09-29-103011-0ec43a04.md)
