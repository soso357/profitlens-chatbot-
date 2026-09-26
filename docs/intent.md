# Intent: ProfitLens website chat agent

Stage 1 artifact (AI-native SDLC). Owner: Ioseb, on behalf of the founders (Sophie, Leli, Tamuna).
Source: profitlens-chat-agent-full-prompt-with-architecture.md (the founders' original brief, kept unchanged in the repo root).
Changes to this file need Ioseb's approval. Everything downstream (spec, plan, code) must trace back to a line here.

## The problem

ProfitLens (useprofitlens.com) is a done-for-you restaurant food cost analysis service for independent US restaurants. Visitors arrive with questions and there is no one awake to answer them: the founders are in Georgia (GMT+4) and visitors are US restaurant owners. Interested owners have to find the booking path themselves, and questions the website does not answer go nowhere.

## What we want

A chat widget on the website that:

1. Answers visitor questions about the service using an approved answers file written by the founders, and nothing else.
2. Asks a short set of qualifying questions about the restaurant.
3. Books the 15 to 20 minute intake call directly in a founder's Google Calendar and notifies the founders.
4. For anything it cannot answer from the approved file, collects the visitor's email and hands off to a founder.

## What we explicitly do not want

It does not sell, negotiate, quote report results, take payment or give business advice. No payment ever happens through the chatbot (confirmed by Ioseb, 2026-09-22). Human steps stay human: the intake call, rescheduling, pricing questions, complaints, payment, advice.

## Why this matters (risk)

Inventing a policy, price, timeline or guarantee is the worst possible defect, because companies have been held legally liable for chatbot statements. Report figures on the website have documented defects, so the chatbot must never repeat any figures.

## Architecture as the founders described it

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

## How we will know it worked

- Founders approve the widget on a hidden test page, then on the live homepage.
- A founder completes a test conversation and booking following only the README.
- No transcript in the first month contains an invented policy, price, promise or figure (founders read every transcript weekly).

## Inputs still needed from the founders

- Anthropic API key with a monthly spend limit set.
- The Google account whose calendar holds the calls, working hours and time zone for calls.
- The Zoho Mail address and app password for notifications (for example info@useprofitlens.com).
- Which founder receives booking notifications.
- Founder edits of content/approved-answers.md, content/qualifying-questions.md, content/handoff-rules.md.

## Change history

Maintain step of the loop (ADR 0020): at every phase gate Ioseb is asked whether anything here changed. Each change gets a dated line; a change here starts a new loop (spec, plan, build).

- 2026-09-22: First version, approved by Ioseb.
