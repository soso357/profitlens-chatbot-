# ProfitLens Website Chat Agent: Claude Code build prompt

How to use this file: open the project folder in VS Code, start Claude Code, paste the "Session opener" block first, then one phase at a time. Do not paste the next phase until the current one has been demonstrated and you have said "approved". Claude Code saves this whole file as CLAUDE.md in the project root.

## Architecture (read this before Phase 0)

Flow, top to bottom: visitor on useprofitlens.com, chat widget (embedded in Framer, says it is an AI), chat service on Render (Python, FastAPI). Inside the service: Claude API runs the conversation and asks qualifying questions; the approved answers file written by the founders is the only source of answers; guardrails in code block report figures and promises and enforce rate limits and a daily spend cap. Three outputs: Google Calendar (books the intake call directly, Google Meet link, US time zone), a leads file (every lead, fit or not, weekly digest to founders), and a founder notified by Zoho email for every booking and for anything off-list. Human steps stay human: the intake call, rescheduling, pricing questions, complaints, payment, advice.

```
                 Restaurant owner (visitor)
                            |
                   Chat widget on the site
                            |
   +------------------------------------------------------+
   |         Chat service on Render (Python, FastAPI)      |
   |                                                      |
   |   Claude API        Approved answers      Guardrails |
   |   runs the chat     founder-written       in code    |
   +------------------------------------------------------+
          |                    |                    |
   Google Calendar        Leads file        Founder by email
   books the call      weekly digest     notified or takes over
```

---

## Session opener (paste first, every new session)

You are building a website chat agent for ProfitLens (useprofitlens.com), a done-for-you restaurant food cost analysis service for independent US restaurants, run by three founders (Sophie, Leli, Tamuna) with Ioseb leading marketing. The agent lives as a chat widget on the website. Its only jobs are:

1. Answer visitor questions about the service using an approved answers file written by the founders, and nothing else.
2. Ask a short set of qualifying questions about the restaurant.
3. Book the 15 to 20 minute intake call directly in a founder's Google Calendar and notify the founders.
4. For anything it cannot answer from the approved file, collect the visitor's email and hand off to a founder.

It does not sell, negotiate, quote report results, take payment, or give business advice.

Project location: ~/Desktop/PROFITLENS-CHATBOT (Mac). The original plan said D:\Thursday- business\profitlens-chat-agent (Windows); changed because the build runs on a Mac. Save this prompt as CLAUDE.md at the start of Phase 0 and keep it updated with decisions made during the build.

The person you are working with is not a software engineer. Explain every technical term the first time you use it, in one plain sentence. When you must choose between approaches, present two or three options with pros and cons in plain English and wait for a choice. Never make a design decision silently.

### Non-negotiable rules

1. The agent answers only from content/approved-answers.md. If the answer is not there, it says so, offers to have a founder email the visitor, and asks for their email. It never fills gaps with plausible text. Inventing a policy, price, timeline or guarantee is the worst possible defect (companies have been held legally liable for chatbot statements).
2. The agent never states report results, savings amounts, profit figures, percentages or example numbers, even if they appear on the website. Founders have documented defects in those figures.
3. The first message tells the visitor they are chatting with an AI assistant for ProfitLens and that a founder handles the actual call. No pretending to be human, ever.
4. No dashes (em-dash or en-dash) in anything the agent writes or in any UI text. Use commas, periods or parentheses.
5. Plain restaurant-owner language. No finance jargon, no "contribution margin", no "prime cost".
6. Short replies. Two to four sentences unless the visitor asks for detail. One question at a time.
7. Secrets (Anthropic API key, Google credentials, email password) live only in environment variables, never in code, never in git. .gitignore covers .env and all credential files.
8. Cost and abuse protection: rate limit per visitor (for example 20 messages per hour per session), cap conversation length, cap tokens per reply, and set a hard daily API spend limit in code that turns the widget into a "leave your email" form when reached.
9. Privacy: store only what is needed (conversation transcript, name, restaurant, email, booking). Transcripts are deleted after 30 days automatically. Note in Phase 5 that the website privacy policy must be updated to mention the chat.
10. Stack: Python 3.11+, FastAPI for the web service, the official anthropic Python library, Google Calendar API via a service account, email via Zoho Mail SMTP (EU servers, .zoho.eu addresses). Front end: one self-contained HTML plus JavaScript widget file served by the same service. Hosting: Render. If a different library is needed, ask first.
11. The widget goes live on useprofitlens.com only after founders approve it on a hidden test page. Until then it runs on the Render URL alone.
12. At the end of every phase: run it, show it working, list what you could not do and why, then stop and wait for the word "approved".
13. One-pass builds are not acceptable. Test each phase with at least ten realistic visitor conversations (including rude, off-topic and trick questions) before demonstrating.

### Things to ask the founders for (collect in Phase 0)

- Anthropic API key (platform.claude.com) with a monthly spend limit set.
- The Google account whose calendar will hold the calls (likely the shared team Google account) and the working hours and time zone for calls. Founders are in Georgia (GMT+4), visitors are US restaurant owners; the agent must show slots in the visitor's US time zone.
- The Zoho Mail address and app password for sending notifications and confirmations (for example info@useprofitlens.com).
- Which founder receives booking notifications.
- The text of the website pages (homepage, how it works, get started, sample, pricing) as source material for the approved answers draft.

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

---

## Decisions already made (do not reopen without a founder)

- Custom build with Claude Code, not an off-the-shelf chat tool.
- Hosted on Render.
- The agent books calls directly in Google Calendar and notifies a founder; rescheduling is done by a founder.
- The agent answers only from the founders' approved answers file; no report figures ever.
- Goes live only after founder approval on a hidden test page.
- The agent never takes payment, never negotiates, never gives advice.

## Build log (decisions made during the build)

- 2026-09-22: Project built on Mac at ~/Desktop/PROFITLENS-CHATBOT instead of the Windows D: drive path. Python 3.12.
- 2026-09-22: Phase 0 started. Folder, virtual environment, requirements.txt, .gitignore, .env.example and git created.
- 2026-09-22: Website text downloaded directly from useprofitlens.com instead of being pasted. content/approved-answers.md drafted from it; report figures, percentages and sample numbers left out on purpose.
- 2026-09-22: Confirmed by Ioseb: no payment ever happens through the chatbot. The chatbot only has conversations and schedules the intake call. No card details, no payment links; payment questions go to a founder.
