# ADR 0018: Conversations survive a server restart (sealed copy in the browser)

- Status: Accepted
- Date: 2026-09-25
- Decided by: Ioseb ("fix so a conversation survives")

## Context

A founder testing on the hidden page answered "food" and Jelena started over with her introduction. Sessions lived only in server memory, and Render restarts the service on every deploy and, on the free plan, after 15 quiet minutes. Options: (1) a paid plan with a disk or a database for sessions, still exposed to lost state on restart between writes; (2) the browser keeps a copy of the conversation that the server signs, so the server can rebuild the session after any restart, with no extra service or cost.

## Decision

Option 2. After every reply the server returns `state`: the conversation and booking state, compressed and sealed with an HMAC signature (SESSION_SECRET, or derived from the API key if not set). The widget stores it in sessionStorage and sends it back with every request. If the session is missing from memory, the server rebuilds it from a valid copy. Copies that were changed, belong to another session, or are older than 24 hours are ignored. app/session_store.py, tests/check_sessions.py.

## Consequences

Conversations continue across deploys and free plan sleeps. A visitor cannot inject fake replies (the seal breaks). Changing SESSION_SECRET or the API key invalidates open copies (those conversations start over once). Still in memory only and lost on restart: per session hourly rate limit counters and the daily spend counter (free plan has no disk); the Anthropic prepaid balance with auto reload off remains the hard spending cap. The 30 minute Telegram copy of each conversation (ADR 0015) does not fire if the free service sleeps first.
