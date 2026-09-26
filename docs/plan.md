# Plan: build phases

Stage 3 artifact. The phase text below is the founders' brief, unchanged. Claude updates only the per phase notes; status is in docs/progress.md.
Rule R12: at the end of every phase, run it, show it working, list what could not be done and why, then stop and wait for "approved" (skill: phase-gate).
Before any code inside a phase, Claude writes a short implementation plan for that phase under "Phase notes" (files touched, order, tests) and gets it approved.

## Status

The phase status table lives in docs/progress.md (ADR 0023 C1). This file holds the phases and the per phase plans.

## Phase notes

(Per phase implementation plans go here, newest phase first.)

### Foundation v2 step 2: session summaries sorted into project files, memory staleness (2026-09-26, ADR 0022; WAITING FOR APPROVAL)
1. The summarizer also writes a small "Routed" block: work done, open questions (with who must answer), people we wait on, decisions, lessons, and changes to plan, spec, ADRs or rules.
2. New script distribute.py, run right after each summary (one at a time, even with parallel terminals):
   - done, open questions, waiting on people: added to docs/progress.md automatically, one line each, ending with the source summary's name so any wrong line can be traced and removed. Items already there are not added twice.
   - lessons: added to memory/procedural/lessons.md automatically; if the same lesson appears a second time, a rule proposal is created.
   - decisions: if docs/build-log.md has no matching line, a proposal "record this decision" is created (Ioseb confirms; nothing is written to ADRs automatically).
   - changes to plan, spec, ADRs or rules: become proposals, never edited automatically.
3. On resume, Claude tidies progress.md: removes questions already answered and done items older than 30 days (moves them nowhere; git keeps history).
4. Staleness: files in memory/semantic/ get a "last verified" date line; the resume brief and recall search flag any older than 60 days. Deferred proposals come back after 30 days. Handoffs marked done are deleted after 14 days.
5. Tests, offline with the fake claude command: routed items land in the right file; duplicates skipped; lesson twice gives a rule proposal; plan change gives a proposal and plan.md is untouched; a broken Routed block changes nothing and is reported; two summaries at once do not corrupt progress.md; stale flags and cleanup. Then evals, /code-review, pull request.

### Foundation v2 step 1: handoff protocol, progress.md, resume, worktrees (2026-09-26, ADR 0022 and 0023; approved by Ioseb 2026-09-26)
1. Shared location: handoffs live in the main project folder even when a terminal works in a worktree (scripts find it through git). New folder memory/working/handoffs/, one file per task, plus a generated _index.md (task, type, branch, updated, open or done). The old handoff.md becomes handoffs/phase-5-launch.md.
2. handoff skill rewritten: the fixed one page template (foundation-v2 section 1.3), records the git commit it was written at, sets Status done when the task is finished. Fix sessions also write memory/incidents/YYYY-MM-DD-slug.md with a required test line; the lesson goes to lessons.md.
3. New resume skill: lists open handoffs, Ioseb picks one, Claude reads it, docs/progress.md and the files it names, shows what other terminals committed since, then says in three lines where it is. The plan status, proposals and summary warnings move here from the start brief.
4. session_start.py: a new session gets only "Say resume to continue a task" (plus a failed summary warning, if any). After a compaction it reinjects this session's own task handoff, not another terminal's.
5. context_guard.py and statusline.py: 60% yellow "handoff" and a nudge to update the task handoff; 70% red "new terminal" and a soft stop (finish the step, update the handoff, commit, tell Ioseb to open a new terminal and say resume). Any compaction: recommend a new terminal at once.
6. settings.json: automatic compaction moves from 70 to 85 (safety net only).
7. docs/progress.md created (current phase, done, in progress, open questions, waiting on people, known problems). The status table moves there from plan.md; plan.md links to it.
8. New parallel-task skill: creates a git worktree (a sibling folder on its own branch) for a second terminal and says which command to run there. Note: .env is not copied into worktrees, so live runs stay in the main folder; offline evals work anywhere.
9. Docs: workflow.md sections 2 and 3, memory/README.md, CLAUDE.md sessions and compact instructions; ADR 0012 marked partly superseded by 0022.
10. Tests: tests/check_workflow.py extended, offline: new session gets one line only; compaction reinjects the right task's handoff when two exist; 60 and 70 nudges fire once each; index lists open and hides done; handoffs found from inside a worktree; statusline colours. Then tests.evals --offline, /code-review, pull request.

### Phase 5 alert check, proposal 0013 (2026-09-26, Ioseb chose: warn through the other channel, ADR 0021)
1. app/alert_health.py: remembers the last result per channel (telegram, email): ok or failing, the reason, the time. Kept in memory only; no visitor data in it.
2. app/telegram.py and app/email_alerts.py keep the failure reason instead of throwing it away (Telegram's own error text, including the new chat ID when a group was upgraded; for email, missing sign-in file or the Google error). Tokens are never written into a reason.
3. On failure, a warning goes through the other channel: Telegram broken, the founders get an email; email broken, a Telegram message. At most once an hour per channel. The warning says what broke, the reason, and what to do (for example "update TELEGRAM_CHAT_ID on Render to -100...").
4. At startup: check that TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FOUNDER_NOTIFY_EMAIL and the Google sign-in file are present, and ask Telegram whether the chat exists (getChat: posts nothing). Problems follow step 3.
5. /health gains "alerts": ok or failing per channel, without the reason text (the page is public).
6. Tests: tests/check_alerts.py, offline, with fake Telegram and Gmail: wrong chat ID, missing token, missing sign-in file, both broken, warning sent once an hour, nothing secret in reasons or /health. Added to tests/evals.py.

### Phase 4 website widget (2026-09-23)
1. app/static/widget.js, served at /widget.js: one self contained file (styles and markup built by the script). Framer embed is one script tag; the widget finds the service address from its own src.
2. Launcher button bottom right, panel over the page, full screen under 480px wide. Geist (inherited from the site, nothing loaded from third parties), body text #666666, no emoji. First message is the AI disclosure, sent by the server (POST /start) so rule R3 is enforced in code.
3. Session id and the visible conversation live in sessionStorage: kept while the visitor moves between pages, gone when the tab closes. No cookies.
4. Time buttons and "Other times" (POST /book). "Leave your email" form when the service says mode email_form (spend cap, rate limit, errors, kill switch later): POST /leave-email saves a lead and alerts founders.
5. CORS: only ALLOWED_ORIGINS (default useprofitlens.com and www) may call the service.
6. Test without the API key: TEST_PAGES=1 plus MODEL_VIA_CLAUDE_CODE=1 makes the local service get replies from Haiku through the Claude Code login. /widget-test is a local page that embeds the widget like Framer will.
7. docs/framer-embed.md: the exact snippet, where to paste it in Framer, and the hidden test page steps.

### Phase 2 leads and alerts (2026-09-23)
1. app/leads.py saves one row per lead to leads.csv (DATA_DIR): time, session, name, restaurant, location, email, fit, outcome (booked, not a fit, founder needed, times offered but not booked), booked time.
2. The model signals a not a fit visitor or a handoff with a hidden <lead>{...}</lead> block once it has their email; code saves the lead and sends "Chat handoff: founder needed" (or "New lead: not a fit") by Telegram and email with the conversation.
3. Bookings save a "booked" lead. A fit visitor who saw times but did not pick one is saved as "times offered, not booked" when the conversation goes quiet.
4. Every conversation goes to Telegram after 30 quiet minutes (ADR 0015). The preview tool sends it when you type quit.
5. Tests: offline checks for lead saving and the conversation digest; preview runs for a not a fit visitor, a handoff and a booking.

### Phase 3 booking in the chat (2026-09-23, Ioseb chose to build it before Phases 1 and 2 are approved)
1. app/chat_booking.py: when the model has name, restaurant, city and state, email and a fit (or unclear) result, it ends its reply with a hidden <offer_times>{...}</offer_times> block. The service strips it, reads the calendar and returns 3 times in the visitor's US time zone (default Eastern). The model never writes times or says a call is booked; only code does (guards R1).
2. Visitor clicks a time (POST /book) or types 1, 2 or 3. Code re-checks the time, books it with a Meet link (app/booking.py), Google emails the invite, founders get Telegram and email alerts with details, fit result and a short transcript.
3. "Other times" shows the next 3. Time taken: new times offered. Calendar down: apology, ask for preferred times, founder alert (spec B11).
4. System prompt job 3 changed from "a founder will email you" to this flow. test-chat page shows time buttons; tests/preview_chat.py lets you type 1, 2 or 3.
5. Tests: offline checks for the signal parsing and time zone fallback; a real booking from the preview.

---

## Phase 0: Setup and approved answers

1. Create the project folder, a Python virtual environment, requirements.txt (fastapi, uvicorn, anthropic, python-dotenv, google-api-python-client, google-auth, pydantic, slowapi for rate limiting), .gitignore, and initialise git.
2. Save this prompt as CLAUDE.md.
3. Ask me for the items under "Things to ask the founders for" and wait for the website text and the calendar details at minimum.
4. Draft content/approved-answers.md from the website text: one section per question a restaurant owner might ask (what the service is, what it costs, what they must send, how long it takes, what they get, who is behind it, how data is handled, how to book). Every answer is a plain statement the founders can edit. Mark any answer you were unsure about with "FOUNDER TO CONFIRM". Do not include any savings, profit or percentage figures. Show me the file and stop until the founders have edited and returned it.
5. Draft content/qualifying-questions.md: the questions the agent will ask, in visitor-friendly wording, based on the founders' criteria: restaurant is food-focused, casual or mid-scale, one to three locations, owner is involved in menu pricing, at least 15 dishes, currently open. Also collect name, restaurant name, city and state, email. Show me and wait.
6. Draft content/handoff-rules.md: when the agent must stop and hand off (any question outside the approved file, pricing negotiation, complaints, requests for advice, anything about report figures, abusive messages).

Demonstrate: the folder exists, the three content files are drafted. Stop and wait for "approved".

---

## Phase 1: The chat service (local only)

1. Build the FastAPI service with one endpoint, POST /chat, that receives a session id and the visitor's message, keeps the conversation history per session in memory (a simple dictionary is fine for now), calls the Anthropic API with a system prompt built from the rules above plus the three content files, and returns the reply.
2. Use a cost-efficient current Claude model (Sonnet or Haiku class). Present me the choice with cost per conversation for each and wait.
3. Implement the guardrails in code, not only in the prompt: a check that blocks replies containing dollar amounts or percentages unless they appear verbatim in the approved answers file; a check that the AI disclosure is present in the first reply; the message and token caps; the daily spend cap.
4. Write tests/conversations.md with at least 15 scripted visitor conversations covering: normal questions, a question not in the approved file, a request for savings numbers, an attempt to make the bot promise results, an angry visitor, a visitor who asks if it is a human, a non-restaurant visitor, a chain restaurant, and off-topic chat. Run all of them and show me the transcripts.
5. Log every conversation to a local file with timestamp and session id.

Demonstrate: run the service locally, show the 15 transcripts, and show the guardrails catching at least three violations. Stop and wait for "approved".

---

## Phase 2: Qualification and lead capture

1. Add the qualifying flow: after the visitor's questions are answered, or when they say they want the analysis or a call, the agent asks the questions from content/qualifying-questions.md one at a time and stores the answers in the session.
2. Score the answers. If the restaurant does not fit (for example a chain, a bar, or not yet open), the agent politely says ProfitLens is built for independent restaurants and offers to pass their details to a founder anyway. It never argues.
3. Save every lead (fit or not) to leads.csv on the server with all answers and the transcript reference.
4. Send a notification email to the founder address via Zoho SMTP for every lead: name, restaurant, city, email, fit result, and the transcript. Emails must be short and plain.
5. Handoff path: whenever the handoff rules trigger, the agent collects the email (if not already known) and sends the same notification with subject "Chat handoff: founder needed".

Demonstrate: three test conversations produce three leads in the CSV and three emails in the founder inbox. Stop and wait for "approved".

---

## Phase 3: Booking in Google Calendar

1. Walk me through creating a Google Cloud project, enabling the Calendar API, creating a service account, downloading its key file (git-ignored), and sharing the founders' booking calendar with the service account email with "make changes to events" permission. One step at a time with screenshots described in words.
2. Read free slots from that calendar within the founders' stated working hours, and present them to the visitor in their US time zone (ask the visitor for their state or city and map to a time zone; default to Eastern if unknown). Offer at most three slots at a time.
3. When the visitor picks a slot, create the event with a Google Meet link, the visitor as guest, the restaurant name in the title, and the lead details plus transcript summary in the description.
4. Send a confirmation email to the visitor and a notification to the founder. Include the founder's reschedule instruction (reply to this email) instead of letting the agent reschedule.
5. Handle failures gracefully: if the calendar cannot be reached, the agent apologises, collects the email and preferred times, and sends a handoff email. Never leave the visitor without a path.

Demonstrate: a test booking appears in the calendar with a Meet link, both emails arrive, and a forced calendar failure falls back correctly. Stop and wait for "approved".

---

## Phase 4: The website widget

1. Build one self-contained widget file (HTML, CSS and JavaScript in one) served by the FastAPI service at /widget.js, so the Framer embed is a single short script tag (Framer custom code blocks are limited to 5,000 characters, so the widget itself must not be pasted into Framer).
2. Design: small launcher button bottom right, chat panel that opens over the page, mobile friendly. Typography to match the site: Geist font, body text #666666, otherwise minimal. No emoji. The first message carries the AI disclosure.
3. Sessions: generate a session id in the browser and keep it for the visit only (no tracking cookies). No third-party scripts.
4. Security: the service only accepts requests from useprofitlens.com and the Render test URL (CORS), and all secrets stay on the server.
5. Provide the exact embed snippet for Framer with the breakpoint noted, plus a hidden test page approach so founders can try it before it goes on the homepage.

Demonstrate: the widget working end to end on the local service, on desktop and a narrow mobile width. Stop and wait for "approved".

---

## Phase 5: Deploy, harden, hand over

1. Walk me through deploying to Render: creating the web service from the git repository, setting environment variables (API key, Google credentials, Zoho password, allowed origins), and choosing the smallest paid instance if the free tier's sleep delay makes the first reply too slow. State the monthly cost.
2. Move conversation logs and leads.csv to persistent storage on Render (a disk) and add the 30-day transcript deletion job.
3. Add a kill switch: an environment variable that switches the widget to "leave your email" mode instantly without a redeploy.
4. Add a one-line health check the founders can open in a browser to see the service is up and today's spend.
5. Write README.md for the founders: how to edit the approved answers (and redeploy), how to change calendar hours, how to read leads.csv, how to use the kill switch, what the monthly costs are. Under two pages, plain English, no dashes.
6. Write docs/privacy-policy-addition.md: the paragraph the founders must add to the website privacy policy about the chat (AI assistant, what is stored, 30-day deletion, email use).
7. For the first month live, founders read every transcript weekly. Add a weekly email digest of transcripts to make that easy.

Demonstrate: the service is live on Render, a founder completes a test conversation and booking from the hidden test page following only the README, and the kill switch works. The build is complete when the founders approve the widget for the live homepage.
