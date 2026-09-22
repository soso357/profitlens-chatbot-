# ADR 0002: Host on Render

- Status: Accepted
- Date: 2026-09 (founder brief)
- Decided by: Founders

## Context

The service needs a public URL, environment variables for secrets, and a disk for logs and leads.

## Decision

Host the chat service on Render. Use the smallest paid instance if the free tier's sleep delay makes the first reply too slow.

## Consequences

Monthly hosting cost to be stated in Phase 5. Logs and leads.csv need a Render disk.
