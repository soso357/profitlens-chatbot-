---
title: Project facts
---

# Project facts

Confirmed facts only. Anything unconfirmed goes to docs/spec.md "Open questions", not here.

## Business
- ProfitLens (useprofitlens.com): done for you restaurant food cost analysis for independent US restaurants.
- Founders: Sophie, Leli, Tamuna. Ioseb leads marketing and runs this build.
- Founders are in Georgia (GMT+4). Visitors are US restaurant owners.
- Website is built in Framer. Custom code blocks there are limited to 5,000 characters.
- Site typography: Geist font, body text #666666.

## People and roles in this build
- Ioseb: approves every phase ("approved"), chooses between options, not a software engineer.
- Founders: own content/ (approved answers, qualifying questions, handoff rules) and approve the widget before it goes live.

## Technical setup (dev machine)
- Mac, project at ~/Desktop/PROFITLENS-CHATBOT, Python 3.12, virtual environment in .venv.
- No jq and no GitHub CLI (gh) on this machine; scripts use python3.
- Node is at ~/.local/node/bin (used only for the pyright type checker).
- Claude Code plugins at project scope: skill-creator, claude-md-management, security-guidance, pyright-lsp.

## Booking and email (confirmed 2026-09-22)
- Booking calendar, notification recipient and Zoho sending address: ioseb@useprofitlens.com.
- Calls bookable all 7 days, 19:00 to 03:00 Georgia time (Asia/Tbilisi, no daylight saving).
- Chat model: Claude Haiku 4.5 (ADR 0013).

## Accounts (credentials never written here)
- Anthropic API: pending from founders.
- Google Calendar (service account): pending.
- Zoho Mail SMTP, EU servers (.zoho.eu): pending.
- Render: not created yet.
