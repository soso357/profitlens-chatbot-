# ADR 0015: Every conversation is sent to the founders' Telegram group

- Status: Accepted
- Date: 2026-09-23
- Decided by: Ioseb (chose "every conversation" over "leads only with full chat" and "live, every message")

## Context

ADR 0014 sends Telegram alerts for leads, bookings and handoffs. Ioseb wants to see every conversation the chatbot has. Options offered: leads only with the full chat (recommended, low noise); every conversation once it ends; every message live.

## Decision

When a conversation has been quiet for 30 minutes, the service sends the whole conversation (or the new part, if the visitor came back) to the founders' Telegram group. This includes chats where the visitor left no details. Lead, booking and handoff alerts still go out immediately (ADR 0014). Card numbers are already removed before anything is stored or sent.

## Consequences

More Telegram messages. Visitor conversations now also live in Telegram, outside our 30 day automatic deletion (R9): a bot can only delete its own messages within 48 hours, so founders must clear the group of messages older than 30 days by hand (monthly). The privacy policy addition (Phase 5) must say that chats are shared with the founders through Telegram. Conversations still in memory when the service restarts are not sent.
