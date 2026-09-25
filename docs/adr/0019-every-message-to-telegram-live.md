# ADR 0019: Every chat message goes to Telegram as it happens

- Status: Accepted (replaces the timing in ADR 0015)
- Date: 2026-09-25
- Decided by: Ioseb ("all our conversation must go straight in telegram chat")

## Context

ADR 0015 sent each conversation to the founders' Telegram group after 30 quiet minutes. On Render's free plan the service sleeps after 15 quiet minutes, so those copies were often never sent. Ioseb wants to see conversations immediately.

## Decision

Each exchange (visitor message plus Jelena's reply, button clicks, shown call times, errors) is posted to the group right away, in a background thread so the visitor never waits. The first exchange is marked "New chat", then "Chat", with the last six characters of the session id to tell chats apart. The 30 minute quiet check stays only to save a fit visitor who saw times but did not book as a lead. TELEGRAM_LIVE=0 switches back to the old one message per conversation mode.

## Consequences

Founders see chats live, on any plan. More Telegram messages (one per exchange). Same privacy note as ADR 0015: visitor chats live in Telegram until the founders delete them (monthly).
