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
| 5 Deploy, harden, hand over | IN PROGRESS: live on Render (free plan) at profitlens-chat.onrender.com; next: Framer hidden test page, then 30 day deletion, kill switch, weekly digest, README, privacy text, new API key, paid plan with disk | not approved |
| W Development workflow (memory, hooks, ADRs) | DONE 2026-09-22 | waiting for Ioseb |
| F Foundation v2 (docs/foundation-v2.md) | DONE 2026-09-27: steps 1 to 6 merged (pull requests #3 to #8); step 7 (multi model orchestration) is design only (ADR 0023 C6), switched on later by Ioseb | approved by merging each step |

## Done (newest first)

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
- phase-5-launch (Build, master): take the widget from the hidden test page to the homepage.

## Open questions

- Has TELEGRAM_CHAT_ID on Render been changed to the supergroup ID? (Ioseb)
- Who pays for the Render Starter plan plus disk? (Ioseb, founders)
- Should the chatbot repeat the visitor's email back to catch typos like "gmial.com"? (Ioseb)
- Should the three offered call times be spread over different days? (Ioseb)
- "1 to 3 locations" or "2 to 5 locations", and the "no AI guesswork" wording. (founders, FOUNDER TO CONFIRM in content/)
- What should Jelena do when a visitor writes in Spanish or another non-English language? (founders) (from 2026-09-26-174858-298f6ef5.md)

## Waiting on people

- Ioseb: tell the founders the repository is now public (ADR 0026).
- Founders: approval of the hidden test page https://useprofitlens.com/chat-test.
- Ioseb: a new Anthropic API key (the current one was pasted into a chat).
- Ioseb: Read docs/spec.md and reply 'spec approved' (from 2026-09-26-174904-2f71faae.md)
- Ioseb: Set TELEGRAM_CHAT_ID on Render and redeploy (from 2026-09-26-174904-2f71faae.md)

## Known problems

- Render free plan: leads, logs and the spend counter are lost on every restart until the paid plan with a disk is set up.
