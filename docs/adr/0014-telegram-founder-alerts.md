# ADR 0014: Founder alerts also go to Telegram

- Status: Accepted
- Date: 2026-09-22
- Decided by: Ioseb

## Context

Founders are notified by Zoho email for every lead, booking and handoff (spec B7, Phase 2). Email is easy to miss in real time, and US visitors arrive during the founders' evening and night (Georgia time).

## Decision

Every lead, booking and handoff alert is sent to a founders' Telegram chat and by Zoho email. Email stays the record and the backup. Telegram is alerts only: founders do not reply to visitors from Telegram, visitors chat only on the website, and visitor confirmations stay on email. Telegram is called over plain HTTPS with no new library (R10). Built in Phase 2.

## Consequences

Two new secrets in environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (R7). A Telegram failure must never block the email or the visitor's reply. Telegram messages hold visitor name, restaurant and email, so the founders' chat must stay private (R9).
