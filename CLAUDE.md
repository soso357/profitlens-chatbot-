# ProfitLens website chat agent

An AI chat widget for useprofitlens.com (done for you food cost analysis for independent US restaurants). It answers only from founder approved answers, asks qualifying questions, books the intake call in Google Calendar, and hands everything else to a founder by email. It never sells, negotiates, quotes figures, takes payment or gives advice.

## Working with Ioseb

Ioseb leads marketing, runs this build for the founders (Sophie, Leli, Tamuna), and is not a software engineer.
- Explain every technical term the first time, in one plain sentence. Reuse or extend memory/semantic/glossary.md.
- When choosing between approaches, give two or three options with plain pros and cons and wait. Never make a design decision silently. Record the choice (skill: new-adr).
- Phase gate: when a phase is done, demonstrate it, list what you could not do and why, then stop and wait for "approved" (skill: phase-gate).

## Where things are (read only what the task needs)

| Need | File |
|---|---|
| Why we build this | docs/intent.md |
| What the chatbot must do: rules R1 to R14, behaviours B, code guardrails G | docs/spec.md |
| Phases, current status, per phase plans | docs/plan.md |
| Decisions and why (founder decisions 0001 to 0006 are not reopened without a founder) | docs/adr/ |
| Event log | docs/build-log.md |
| What the chatbot knows (founders own it) | content/ |
| How we work: SDLC loop, context handoff, capability evolution | docs/workflow.md |
| Memory layers and search | memory/README.md |
| Review checklist | REVIEW.md |
| The founders' original brief (history, do not edit) | profitlens-chat-agent-full-prompt-with-architecture.md |

## Hard rules for you

1. The chatbot's rules R1 to R14 in docs/spec.md override convenience. Any rule on what the chatbot says is enforced in code, not only in its prompt.
2. No em dash or en dash in content/, UI text, or anything the chatbot says (a hook checks).
3. Secrets only in environment variables. Never read or print .env or credential files. New libraries need approval.
4. Before writing code in a phase, add a short plan to docs/plan.md "Phase notes" and get it approved.
5. Test with at least ten realistic visitor conversations per phase, including rude, off topic and trick questions.
6. Log every decision as one line in docs/build-log.md (not in this file); design choices also get an ADR. Update the plan status table when a phase moves.
7. Another Claude session may be working in this repo. Re-read shared files right before editing them. Stage files by name, never `git add -A`.
8. Same mistake twice: add it to memory/procedural/lessons.md and propose a rule.

## Commands

```
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload            # run the chat service locally
.venv/bin/python -m tests.check_guardrails         # offline guardrail checks
.venv/bin/python -m tests.run_conversations        # scripted conversations (service must be running)
python3 .claude/scripts/lint_content.py --all      # dashes and percentages in chatbot text
python3 .claude/scripts/memory_index.py search <words>
```

## Sessions and memory (automatic, see docs/workflow.md)

- Start: a hook briefs you with plan status, the last session's next steps, open proposals and any handoff. If the last summary says `reviewed: no`, skim and correct it.
- 60% context: write memory/working/handoff.md (skill: handoff). 70%: auto compaction, handoff reinjected. After 3 compactions tell Ioseb to open a new terminal or /clear.
- End: a background job writes the session summary and improvement proposals to memory/.

## Improving the setup

When you notice something useful Ioseb did not ask for (a repeated task, a spec gap, a missing guardrail or test), record it with the propose-capability skill and mention it in one sentence. Build only what Ioseb approves.
- 2026-09-22: Telegram bot is @profitlbot. Founder alerts group "ProfitLens leads", chat ID -5552197383 (not a secret; stored in .env.example). Test message delivered. Ioseb chose to keep the bot token that was shared in chat rather than revoke it.
- 2026-09-22 (end of day): WHERE WE STOPPED. Phase 1 code is built and offline checks pass (tests/check_guardrails.py). Waiting for Ioseb to create an Anthropic API key and the .env file (he runs: cp .env.example .env, adds the Telegram token and the key). Next: run the 17 conversations (tests/run_conversations.py, start uvicorn with IP_RATE_LIMIT=500/hour), show transcripts and guardrail catches, then wait for "approved". Still open: Ioseb has not said whether he added the .claude/, docs/ and memory/ files.
- 2026-09-22: Phase 3 calendar method changed by Ioseb: "sign in once" (OAuth as the calendar owner) instead of a service account, because on a free Google account a service account cannot add guests or create Meet links. Rule 10 stack note: Google Calendar API via OAuth for the owner's account. Google setup (account, Cloud project, API, sign-in screen) is being done early; booking code still waits for Phases 1 and 2 to be approved.
- 2026-09-22: Booking calendar is profitlenstemplate@gmail.com (Ioseb's choice), not ioseb@useprofitlens.com. Emails and notifications still use ioseb@useprofitlens.com.
- 2026-09-22: Google setup done (Phase 3 step 1). Cloud project "ProfitLens Chatbot" on profitlenstemplate@gmail.com, Calendar API on, sign-in screen published to production (homepage and privacy policy set to useprofitlens.com). One-time sign-in done with scripts/google_signin.py; long-lasting sign-in saved to secrets/google-token.json (git-ignored). Calendar readable. Booking code not written yet (waits for Phases 1 and 2).
- 2026-09-22: Test done: calendar free times found (shown in US Eastern), TEST event created with a Meet link, alert posted to Telegram. Note for Phase 2: Python's built-in urllib fails SSL on this Mac ("self-signed certificate in chain"); use an ssl context from certifi (already installed) for Telegram calls.
- 2026-09-22: Founder email alerts go to ioseb@useprofitlens.com AND profitlenstemplate@gmail.com (Ioseb's request), sent through Zoho from ioseb@useprofitlens.com. Local client test page at /test-booking (only when TEST_PAGES=1) books real calendar events and sends Telegram and email alerts.
- 2026-09-22: Zoho dropped (Ioseb). Rule 10 stack change: founder alert emails are sent through the Gmail API from profitlenstemplate@gmail.com, using the same Google sign-in (gmail.send permission added). Clients get Google Calendar's own invite email with the Meet link. No Zoho app password needed.
- 2026-09-23: Client-side booking test passed (Ioseb): pick time on /test-booking, call created with Meet link, Google invite to client, Telegram alert, Gmail alert to both founder addresses. Test calls left in the calendar for Wed 23 Sep (Ioseb chose to keep them). Next: Anthropic key, then Phase 1 test run.
