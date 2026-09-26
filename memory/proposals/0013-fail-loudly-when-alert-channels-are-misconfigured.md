---
title: Fail loudly when alert channels are misconfigured
status: proposed
kind: hook
source: 2026-09-26-919cea64.md
created: 2026-09-26
---

## Why
Telegram and founder-email alerts silently sent nothing for a period because .env was missing, and later failed silently again when the Telegram group's chat ID changed after adding the founder; both went unnoticed until manually checked.

## What
A startup or pre-send check that verifies required alert env vars are set and that a Telegram send actually succeeds, surfacing a visible warning (in the statusline or a log) instead of failing silently.

## Decision
(pending Ioseb)
