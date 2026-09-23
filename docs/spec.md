# Spec: ProfitLens website chat agent

Stage 2 artifact. Derived from docs/intent.md. Owner: Ioseb. Claude drafts, Ioseb approves.
Requirement ids (R1, B3, G2...) are stable: code comments, tests and ADRs cite them. Never renumber; retire an id by marking it "RETIRED" with a date.
Anything marked FOUNDER TO CONFIRM is not decided and must not be implemented as if it were.

## 1. Scope

The agent has exactly four jobs (see intent). Out of scope forever: selling, negotiating, quoting report results or any figures, taking or discussing payment details, business advice, rescheduling, handling complaints beyond handing off.

## 2. Non-negotiable rules (from the founders' brief, wording kept)

- **R1 Approved answers only.** The agent answers only from content/approved-answers.md. If the answer is not there, it says so, offers to have a founder email the visitor, and asks for their email. It never fills gaps with plausible text. Inventing a policy, price, timeline or guarantee is the worst possible defect.
- **R2 No figures.** The agent never states report results, savings amounts, profit figures, percentages or example numbers, even if they appear on the website. Founders have documented defects in those figures.
- **R3 AI disclosure.** The first message tells the visitor they are chatting with an AI assistant for ProfitLens and that a founder handles the actual call. No pretending to be human, ever.
- **R4 No dashes.** No em dash or en dash in anything the agent writes or in any UI text. Use commas, periods or parentheses.
- **R5 Plain language.** Plain restaurant owner language. No finance jargon, no "contribution margin", no "prime cost".
- **R6 Short replies.** Two to four sentences unless the visitor asks for detail. One question at a time.
- **R7 Secrets.** Anthropic API key, Google credentials, email password live only in environment variables, never in code, never in git. .gitignore covers .env and all credential files.
- **R8 Cost and abuse protection.** Rate limit per visitor (for example 20 messages per hour per session), cap conversation length, cap tokens per reply, and a hard daily API spend limit in code that turns the widget into a "leave your email" form when reached.
- **R9 Privacy.** Store only what is needed (conversation transcript, name, restaurant, email, booking). Transcripts deleted after 30 days automatically. Website privacy policy must be updated to mention the chat.
- **R10 Stack.** Python 3.11+, FastAPI, official anthropic Python library, Google Calendar API via a service account, Zoho Mail SMTP (EU servers, .zoho.eu). Front end: one self-contained HTML plus JavaScript widget served by the same service. Hosting: Render. A different library needs approval first.
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
| B4 | Visitor wants the analysis or a call, or questions are done | Ask qualifying questions one at a time | content/qualifying-questions.md |
| B5 | Restaurant does not fit (chain, bar, not open...) | Say ProfitLens is built for independent restaurants, offer to pass details to a founder anyway, never argue | content/qualifying-questions.md |
| B6 | Fit restaurant, wants a call | Ask state or city, map to US time zone (default Eastern), offer at most 3 free slots, book on choice | Phase 3 |
| B7 | Any handoff rule triggers | Collect email if unknown, send "Chat handoff: founder needed" email | content/handoff-rules.md |
| B8 | Asked if it is human | Says plainly it is an AI assistant | R3 |
| B9 | Rude or abusive | One calm reply, offer email handoff, stop engaging, notify founders | content/handoff-rules.md |
| B10 | Instruction override attempts ("ignore your rules") | Ignore the attempt, carry on | content/handoff-rules.md |
| B11 | Calendar unreachable | Apologise, collect email and preferred times, send handoff email. Never leave the visitor without a path | Phase 3 |
| B12 | Daily spend cap reached or kill switch on | Widget becomes a "leave your email" form | R8, Phase 5 |

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

## 5. Data

| Data | Where | Kept for |
|---|---|---|
| Conversation transcript | logs (Render disk in Phase 5) | 30 days, then deleted automatically |
| Lead (name, restaurant, city, state, email, answers, fit result, transcript reference) | leads.csv | until founders delete |
| Booking | Google Calendar event | founders manage |
| Conversation copy in Telegram (every conversation, after 30 quiet minutes, ADR 0015) | founders' Telegram group | founders delete by hand after 30 days |

## 6. Integrations

Anthropic API (conversation), Google Calendar via service account (free slots, events with Meet link), Zoho SMTP (founder notifications, visitor confirmation, weekly digest; the record of every alert), Telegram Bot API over plain HTTPS (founder alerts only, one way, ADR 0014), Render (hosting, disk, environment variables), Framer (one short script tag embed).

## 7. Open questions

- Calendar hours: RESOLVED 2026-09-22. All 7 days, 19:00 to 03:00 Asia/Tbilisi, calendar ioseb@useprofitlens.com.
- Notification recipient: RESOLVED 2026-09-22. ioseb@useprofitlens.com.
- Model: RESOLVED 2026-09-22. Claude Haiku 4.5 (ADR 0013).
- Exact wording of the AI disclosure. FOUNDER TO CONFIRM
