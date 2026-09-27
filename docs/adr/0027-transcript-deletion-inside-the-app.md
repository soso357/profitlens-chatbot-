# ADR 0027: 30 day transcript deletion runs inside the app

- Status: Accepted
- Date: 2026-09-27
- Decided by: Ioseb (option 1, inside the app)
- Links: decides R9

## Context

R9 says conversation transcripts are deleted automatically after 30 days. Every message is appended to logs/conversations.jsonl and nothing removes old lines. Leads (leads.csv) hold no transcript and are kept until the founders delete them.

Options:
1. Inside the app: clean up at startup, then every 24 hours while it runs. Pros: nothing extra to set up, no cost. Cons: runs only while the service runs (fine, the service is always on).
2. A Render cron job (a small program Render runs on a timer). Pros: independent of the app. Cons: extra cost, and a Render disk attaches to one service only, so the job could not reach the log file.

## Decision

Option 1. On startup and every 24 hours after, the app rewrites logs/conversations.jsonl keeping only lines from the last 30 days.

## Consequences

No extra cost or setup. On the free plan the log is lost on every restart anyway; the cleanup matters once the paid plan with a disk is in place. Copies outside our server are not covered: the Telegram group (founders delete by hand, spec section 5) and lead and handoff alert emails in Gmail, which include the conversation (spec section 5 does not yet say how long those are kept; open question for the founders).
