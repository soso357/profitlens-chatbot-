# Progress: where the project stands now

Project memory (ADR 0022, 0023). What is true right now. Claude keeps it current: at the end of every task, in every handoff, and automatically from session summaries (foundation v2 step 2). Plans are in docs/plan.md, decisions in docs/adr/ and docs/build-log.md.
Rules: overwrite what changed, do not append history (except the Done list). One line per item. Link, do not copy.

## Phases

| Phase | Status | Gate |
|---|---|---|
| 0 Setup and approved answers | DONE | approved 2026-09-22 |
| 1 Chat service (local) | DONE (17 conversations with the real API key, Haiku and Sonnet compared, Sonnet chosen) | approved 2026-09-24 by Ioseb |
| 2 Qualification and lead capture | DONE | approved 2026-09-23 by Ioseb |
| 3 Booking in Google Calendar | DONE | approved 2026-09-23 by Ioseb |
| 4 Website widget | DONE (tested locally via Claude Code; recheck with the API key during Phase 1) | approved 2026-09-23 by Ioseb |
| 5 Deploy, harden, hand over | IN PROGRESS: live on the useprofitlens.com homepage (founders approved, R11), Render Starter plan with 1 GB disk, privacy text published; weekly digest skipped (ADR 0031); next: restart test, phase gate; kill switch skipped by Ioseb 2026-09-27 | not approved |
| W Development workflow (memory, hooks, ADRs) | DONE 2026-09-22 | waiting for Ioseb |
| F Foundation v2 (docs/archive/foundation-v2.md) | DONE 2026-09-27: steps 1 to 6 merged (pull requests #3 to #8); step 7 (multi model orchestration) is design only (ADR 0023 C6), switched on later by Ioseb | approved by merging each step |

## Done (newest first)

- 2026-10-08: Founders approved removing call-time booking from the chat; the chat hands the intake call to a founder by email (ADR 0032, supersedes 0003). Code and tests done, spec 1.7 waits for Ioseb.
- 2026-10-06: Weekly digest email skipped (ADR 0031).
- 2026-10-06: Founders approved the widget; live on the homepage. Privacy policy text published (R9).
- 2026-10-06: Render Starter plan and 1 GB disk set up; leads, logs and spend counter now survive restarts (DATA_DIR, LOG_DIR on /var/data).
- 2026-10-03: Unused workflow tooling removed (summarizer, search index, context graph, closed proposals); chatbot untouched (ADR 0030).
- 2026-09-29: Email typo check (B13): near misses like gmil.com are read back, visitor confirms with yes or retypes; spec 1.5.
- 2026-09-28: Notes tidied: session summary, proposals 0036 to 0040 closed, stray docs/image.png deleted (Ioseb).
- 2026-09-28: Chat asks only first name, restaurant, state, email, then shows times; fit questions removed (B5 retired), G8 blocks "which option?" questions; spec 1.3, ADR 0029 (PR #14, merged).
- 2026-09-28: Sales push check catches "or would you like help getting started?" (proposal 0040, PR #15, merged).
- 2026-09-27: Workflow overhead trimmed (ADR 0028): 6 open proposals, Obsidian map and graph check off by default, worktree for phase-5-launch.
- 2026-09-27: Stale duplicate Obsidian map note resolved and vault shortcuts rebuilt with no data loss (from 2026-09-27-170044-d2856c37.md)
- 2026-09-27: GitHub branch ruleset (require status checks to pass) confirmed active (from 2026-09-27-170037-2f71faae.md)
- 2026-09-27: Automatic summarizer duplicate lines and 6 duplicate proposals cleaned up (from 2026-09-27-170037-2f71faae.md)
- 2026-09-27: Proposal-duplicate matching rewritten to topic-and-choice comparison after a too-loose stem-based version was found by review (from 2026-09-27-170037-2f71faae.md)
- 2026-09-27: 30 day transcript deletion built (R9, ADR 0027); spec 1.1 approved.
- 2026-09-27: Spec 1.0 approved by Ioseb. README for the founders merged (pull request #10).
- 2026-09-27: TELEGRAM_CHAT_ID on Render set to the supergroup; test chat messages reach Telegram (Ioseb confirmed).
- 2026-09-27: Foundation v2 complete. Step 6: context graph (pull request #8). Step 7 stays a design until Ioseb switches it on.
- 2026-09-27: Repository made public (Ioseb, ADR 0026); merges now need the green checks mark.
- 2026-09-26: Foundation v2 step 5: automatic checks on GitHub (pull request #7).
- 2026-09-26: 12 pending proposals reviewed and decided: 0013/0014/0015 approved, 0005 made a standing rule, 0002/0003 deferred, 0004/0007/0008/0009/0010/0011 rejected (from 2026-09-26-174858-298f6ef5.md)
- 2026-09-26: Confirmed live on Render that Telegram and email alert checks both report ok (from 2026-09-26-174858-298f6ef5.md)
- 2026-09-26: Foundation v2 step 4: spec versions, acceptance checks, approval before planning (pull request #6).
- 2026-09-26: Foundation v2 step 3: agent harness, allow/ask/deny lists and guard hook (pull request #5).
- 2026-09-26: Foundation v2 step 2: session summaries sorted into project files, memory staleness (pull request #4).
- 2026-09-26: Foundation v2 step 1: one handoff per task, resume, progress.md, worktrees, incident notes (pull request #3).
- 2026-09-26: Foundation v2 design approved, all recommended options (ADR 0022, 0023).
- 2026-09-26: Alert channels fail loudly (ADR 0021), pull request #2.
- 2026-09-26: Pull request flow with stage labels and evals (ADR 0020), pull request #1.
- 2026-09-25: Founders' approved answers v2 installed; conversations survive restarts (ADR 0018); every message to Telegram live (ADR 0019).

## In progress

Open tasks and their handoffs: memory/working/handoffs/_index.md (say "resume" to pick one).
- phase-5-launch (Build, build-p5-launch): take the widget from the hidden test page to the homepage.
- remove-booking (Build, phase-5-remove-booking): remove call-time booking from the chat (ADR 0032); code done, waiting for spec 1.7 approval.

## Open questions

- How long do founders keep lead and handoff emails in Gmail? They include the chat, outside R9's 30 day deletion (ADR 0027). (founders)
- Should the three offered call times be spread over different days? (Ioseb)
- One FOUNDER TO CONFIRM item in content/: how quickly founders promise to reply (handoff-rules.md). The three fit items went away with the fit questions (ADR 0029). (founders)
- What should Jelena do when a visitor writes in Spanish or another non-English language? (founders) (from 2026-09-26-174858-298f6ef5.md)
- Proposal 0041: run pyright in the offline evals. Approve, reject or later? (Ioseb) (from 2026-09-29-103011-0ec43a04.md)
- Can the finished email-typo-check worktree be deleted? (Ioseb) (from 2026-09-29-103011-0ec43a04.md)

## Waiting on people

- Ioseb: approve spec 1.7 (call booking retired, ADR 0032) so the evals and spec check pass; then run spec_check.py approve.
- Ioseb: tell the founders the repository is now public (ADR 0026).
- Ioseb: tell the founders the fit questions are gone; every visitor can book, they screen on the call (ADR 0029).
- Ioseb: Try the email typo check for free with tests.preview_chat and try useprofitlens.com/chat-test (from 2026-09-29-103011-0ec43a04.md)
- Ioseb: Approve a paid run of the 19 live chats when ready, since chat 19 and the G8 and sales push fixes have no live AI run yet (from 2026-09-29-103011-0ec43a04.md)

## Known problems

- None known.
