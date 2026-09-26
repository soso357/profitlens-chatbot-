---
title: Fail loudly when alert channels are misconfigured
status: built
kind: hook
source: 2026-09-26-919cea64.md
created: 2026-09-26
---

## Why
Telegram and founder-email alerts silently sent nothing for a period because .env was missing, and later failed silently again when the Telegram group's chat ID changed after adding the founder; both went unnoticed until manually checked.

## What
A startup or pre-send check that verifies required alert env vars are set and that a Telegram send actually succeeds, surfacing a visible warning (in the statusline or a log) instead of failing silently.

## Decision
Ioseb, 2026-09-26 (proposal review): approved. Build before go live.
Built 2026-09-26 on branch phase-5-alert-check (ADR 0021): app/alert_health.py, reasons kept in app/telegram.py and app/email_alerts.py, warning through the other channel once an hour, startup check, alerts on /health. tests/check_alerts.py.
