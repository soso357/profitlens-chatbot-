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
| F Foundation v2 (docs/foundation-v2.md) | IN PROGRESS: step 1 of 7 merged (pull request #3); steps 1 and 2 merged; step 3 (agent harness) in pull request, waiting for merge | design approved 2026-09-26 (ADR 0023) |

## Done (newest first)

- 2026-09-26: Foundation v2 step 2: session summaries sorted into project files, memory staleness (pull request #4).
- 2026-09-26: Foundation v2 step 1: one handoff per task, resume, progress.md, worktrees, incident notes (pull request #3).
- 2026-09-26: Foundation v2 design approved, all recommended options (ADR 0022, 0023).
- 2026-09-26: Alert channels fail loudly (ADR 0021), pull request #2.
- 2026-09-26: Pull request flow with stage labels and evals (ADR 0020), pull request #1.
- 2026-09-25: Founders' approved answers v2 installed; conversations survive restarts (ADR 0018); every message to Telegram live (ADR 0019).

## In progress

Open tasks and their handoffs: memory/working/handoffs/_index.md (say "resume" to pick one).
- phase-5-launch (Build, master): take the widget from the hidden test page to the homepage.
- foundation-v2 (Build, maintain-foundation-v2-step2): step 2 of 7.

## Open questions

- Has TELEGRAM_CHAT_ID on Render been changed to the supergroup ID? (Ioseb)
- Who pays for the Render Starter plan plus disk? (Ioseb, founders)
- Should the chatbot repeat the visitor's email back to catch typos like "gmial.com"? (Ioseb)
- Should the three offered call times be spread over different days? (Ioseb)
- "1 to 3 locations" or "2 to 5 locations", and the "no AI guesswork" wording. (founders, FOUNDER TO CONFIRM in content/)

## Waiting on people

- Founders: approval of the hidden test page https://useprofitlens.com/chat-test.
- Ioseb: a new Anthropic API key (the current one was pasted into a chat).

## Known problems

- Render free plan: leads, logs and the spend counter are lost on every restart until the paid plan with a disk is set up.
