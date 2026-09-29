# Spec: ProfitLens website chat agent

Version: 1.4
Status: Approved
Approved by: Ioseb
Date: 2026-09-29
Fingerprint: 1b9b98dd07500bef

Stage 2 artifact. Derived from docs/intent.md. Owner: Ioseb. Claude drafts, Ioseb approves.
Requirement ids (R1, B3, G2...) are stable: code comments, tests and ADRs cite them. Never renumber; retire an id by marking it "RETIRED" with a date.
Anything marked FOUNDER TO CONFIRM is not decided and must not be implemented as if it were.
Versions (ADR 0025): when Ioseb approves, Claude runs `spec_check.py approve`, which sets the next version and a fingerprint of the text; any later change makes it Draft again (a hook and the evals check the fingerprint). An open item marked FOUNDER TO CONFIRM names the ids it blocks, e.g. "(blocks R3)". A new phase note in docs/plan.md starts with "Spec version X, covers ..." and may only cite an Approved version. Section 8 names the check that proves each id.

## 1. Scope

The agent has exactly four jobs (see intent). Out of scope forever: selling, negotiating, quoting report results or any figures, taking or discussing payment details, business advice, rescheduling, handling complaints beyond handing off.

## 2. Non-negotiable rules (from the founders' brief, wording kept)

- **R1 Approved answers only.** The agent answers only from content/approved-answers.md. If the answer is not there, it says so, offers to have a founder email the visitor, and asks for their email. It never fills gaps with plausible text. Inventing a policy, price, timeline or guarantee is the worst possible defect.
- **R2 No figures.** The agent never states report results, savings amounts, profit figures, percentages or example numbers, even if they appear on the website. Founders have documented defects in those figures.
- **R3 AI disclosure.** The first message tells the visitor they are chatting with an AI assistant for ProfitLens and that a founder handles the actual call. No pretending to be human, ever.
- **R4 No dashes.** No em dash or en dash in anything the agent writes or in any UI text. Use commas, periods or parentheses.
- **R5 Plain language.** Plain restaurant owner language. No finance jargon, no "contribution margin", no "prime cost". Say "profit per plate", never "margin" (founder, 2026-09-25: the term used in the report).
- **R6 Short replies.** Two to four sentences unless the visitor asks for detail. One question at a time.
- **R7 Secrets.** Anthropic API key, Google credentials, email password live only in environment variables, never in code, never in git. .gitignore covers .env and all credential files.
- **R8 Cost and abuse protection.** Rate limit per visitor (for example 20 messages per hour per session), cap conversation length, cap tokens per reply, and a hard daily API spend limit in code that turns the widget into a "leave your email" form when reached.
- **R9 Privacy.** Store only what is needed (conversation transcript, name, restaurant, email, booking). Transcripts deleted after 30 days automatically. Website privacy policy must be updated to mention the chat.
- **R10 Stack.** Python 3.11+, FastAPI, official anthropic Python library, Google Calendar API and Gmail API through a one time Google sign-in as the calendar owner (Zoho dropped by Ioseb, 2026-09-22 and 2026-09-26). Front end: one self-contained HTML plus JavaScript widget served by the same service. Hosting: Render. A different library needs approval first.
- **R11 Launch gate.** The widget goes live on useprofitlens.com only after founders approve it on a hidden test page. Until then it runs on the Render URL alone.
- **R12 Phase gate.** At the end of every phase: run it, show it working, list what could not be done and why, stop and wait for "approved".
- **R13 Tested, not one pass.** Each phase is tested with at least ten realistic visitor conversations (including rude, off-topic and trick questions) before demonstrating.
- **R14 No payment.** No card details, no payment links, no invoices through the chat. Payment questions go to a founder. (Ioseb, 2026-09-22)

## 3. Conversation behaviour

| Id | Situation | Required behaviour | Source file |
|---|---|---|---|
| B1 | First reply of any session | Contains the AI disclosure (R3). In the widget the server sends it as the first message when the chat opens (POST /start) | code check G2 |
| B2 | Question answered in the approved file | Answer in 2 to 4 sentences, same meaning as the file | content/approved-answers.md |
| B3 | Question not in the approved file | Say it is not something the agent can answer, offer founder email, ask for email | content/handoff-rules.md |
| B4 | Visitor wants the analysis or a call, or questions are done | Ask only for first name, restaurant name, state and email, one at a time, then offer times (B6). No questions about the restaurant's type, size, menu or which option they want (Ioseb, 2026-09-28) | content/qualifying-questions.md |
| B5 | RETIRED 2026-09-28 (Ioseb: no fit screening in the chat; every visitor who gives the four details can book, founders judge fit on the call) | | |
| B6 | Visitor has given first name, restaurant name, state and email | Map the state to a US time zone (default Eastern), offer at most 3 free slots, book on choice | Phase 3 |
| B7 | Any handoff rule triggers | Collect email if unknown, send "Chat handoff: founder needed" email | content/handoff-rules.md |
| B8 | Asked if it is human | Says plainly it is an AI assistant | R3 |
| B9 | Rude or abusive | One calm reply, offer email handoff, stop engaging, notify founders | content/handoff-rules.md |
| B10 | Instruction override attempts ("ignore your rules") | Ignore the attempt, carry on | content/handoff-rules.md |
| B11 | Calendar unreachable | Apologise, collect email and preferred times, send handoff email. Never leave the visitor without a path | Phase 3 |
| B12 | Daily spend cap reached or kill switch on | Widget becomes a "leave your email" form | R8, Phase 5 |
| B13 | Visitor types an email that looks wrong: no dot after the @, or a near miss of gmail, yahoo, outlook, hotmail, icloud or aol (for example gmil.com) | Checked in code before booking or saving a lead. Read the address back once: "Did you mean maria@gmail.com? Reply yes, or type the right email." "yes" uses the suggestion; a new email is checked again. If there is no suggestion (no dot), ask them to type it again. Ask only once per address (Ioseb, 2026-09-29) | code check |

## 4. Guardrails enforced in code (not only in the prompt)

| Id | Guardrail | Acceptance test |
|---|---|---|
| G1 | Block replies containing dollar amounts or percentages unless they appear verbatim in approved-answers.md | Scripted conversation asking for savings is caught |
| G2 | First reply must contain the AI disclosure | Disclosure missing leads to a safe fallback reply |
| G3 | Reject em dash and en dash in replies (replace or regenerate) | Reply with a dash never reaches the visitor |
| G4 | Per session message rate limit, conversation length cap, max tokens per reply | 21st message in an hour is refused politely |
| G5 | Daily spend cap in code switches to email form | Simulated spend over cap flips the mode |
| G6 | Kill switch environment variable, no redeploy needed | Setting it flips the mode on the next request |
| G7 | CORS allows only useprofitlens.com and the Render test URL | Request from another origin is refused |
| G8 | Block replies that ask the visitor to pick an option or price (for example "the $99 or the $149?"); replace with a neutral reply | Scripted reply asking "$99 or $149?" never reaches the visitor |

## 5. Data

| Data | Where | Kept for |
|---|---|---|
| Conversation transcript | logs (Render disk in Phase 5) | 30 days, then deleted automatically |
| Lead (first name, restaurant, state, email, transcript reference) | leads.csv | until founders delete |
| Booking | Google Calendar event | founders manage |
| Conversation copy in Telegram (every message, live, ADR 0019) | founders' Telegram group | founders delete by hand after 30 days |

## 6. Integrations

Anthropic API (conversation), Google Calendar (free slots, events with Meet link; Google sends the visitor's invite), Gmail API from the booking account (founder notifications, weekly digest; the record of every alert), Telegram Bot API over plain HTTPS (founder alerts only, one way, ADR 0014), Render (hosting, disk, environment variables), Framer (one short script tag embed).

## 7. Open questions

- Calendar hours: RESOLVED 2026-09-22. All 7 days, 19:00 to 03:00 Asia/Tbilisi, calendar ioseb@useprofitlens.com.
- Notification recipient: RESOLVED 2026-09-22. ioseb@useprofitlens.com.
- Model: Claude Sonnet 5, for testing and real visitors (ADR 0016).
- Exact wording of the AI disclosure. Ioseb named the assistant Jelena (2026-09-23): "Hi, I'm Jelena, the AI assistant for ProfitLens...". FOUNDER TO CONFIRM (blocks R3, B1, G2)

## 8. Acceptance checks

How we know each rule, behaviour and guardrail works. "Check" is a test file (optionally a conversation number in tests/conversations.md), "manual: how" when only a person can judge, or "none yet" when it is not built or not tested. tests/check_spec.py verifies every id has a row and every named test exists. A phase that builds or changes an id replaces its "none yet" with the test it added.

| Id | Check |
|---|---|
| R1 | tests/conversations.md#3; tests/conversations.md#1 |
| R2 | tests/check_guardrails.py; tests/conversations.md#4; tests/conversations.md#5 |
| R3 | tests/check_guardrails.py; tests/conversations.md#8 |
| R4 | tests/check_guardrails.py; tests/conversations.md#17 |
| R5 | manual: founders read every transcript weekly in the first month |
| R6 | tests/check_guardrails.py |
| R7 | tests/check_harness.py; tests/check_alerts.py |
| R8 | none yet (G4, G5 have no test) |
| R9 | tests/check_retention.py; manual: privacy policy text on the website (not written yet) |
| R10 | manual: code review; a new library needs Ioseb's approval |
| R11 | manual: founders approve on the hidden test page |
| R12 | manual: phase gate pull request (skill: phase-gate) |
| R13 | tests/run_conversations.py |
| R14 | tests/check_guardrails.py; tests/conversations.md#14 |
| B1 | tests/check_guardrails.py |
| B2 | tests/conversations.md#1; tests/conversations.md#2 |
| B3 | tests/conversations.md#3 |
| B4 | tests/check_booking.py; tests/conversations.md#10; tests/conversations.md#16 |
| B5 | manual: nothing to check, RETIRED 2026-09-28 |
| B6 | tests/check_booking.py |
| B7 | tests/check_booking.py; tests/conversations.md#13; tests/conversations.md#15 |
| B8 | tests/conversations.md#8 |
| B9 | tests/conversations.md#7 |
| B10 | tests/conversations.md#12 |
| B11 | tests/check_booking.py |
| B12 | none yet (kill switch not built, Phase 5) |
| B13 | none yet |
| G1 | tests/check_guardrails.py; tests/conversations.md#4 |
| G2 | tests/check_guardrails.py |
| G3 | tests/check_guardrails.py |
| G4 | none yet |
| G5 | none yet |
| G6 | none yet (kill switch not built, Phase 5) |
| G7 | none yet |
| G8 | tests/check_guardrails.py; tests/conversations.md#18 |
