# ADR 0029: Four contact details, no fit screening in the chat

- Status: Accepted
- Date: 2026-09-28
- Decided by: Ioseb (option "book anyway")
- Links: decides B4, B5, B6, G8

## Context

Ioseb asked to drop the five fit questions (bar or restaurant, casual or mid range, locations, who sets prices, menu size) and the model-invented "the $99 or the $149?" question, keeping only first name, restaurant, state and email before the call times. Open point: what to do when a visitor volunteers that they run a bar or a chain. Options: book anyway (simplest, founders judge on the call); book but flag it in the founder alert (small extra work); do not book and hand off (keeps old B5 behaviour for volunteered non fits).

## Decision

Book anyway. Every visitor who gives the four details gets call times. B5 is retired. A code guardrail (G8) removes any reply sentence asking the visitor to choose an option or price, keeping founder offers.

## Consequences

Fewer questions, less drop off before booking. Founders may get intake calls with bars, chains or larger groups and must screen on the call. leads.csv keeps an empty "fit" column so older files still read. The founders' content/qualifying-questions.md was changed at Ioseb's request (listed in PR #14).
