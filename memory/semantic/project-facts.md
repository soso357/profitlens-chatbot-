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
- Obsidian vault ~/Desktop/IOSEB/IOSEB has a folder "PROFITLENS CHATBOT" of live links (symlinks) to docs/, memory/, content/, .claude/rules, .claude/skills, CLAUDE.md, REVIEW.md, the founders' brief, and (in a code subfolder) app/, tests/, scripts/, .claude/scripts, settings.json, requirements.txt, .env.example, .gitignore. Never linked: .env, secrets/, logs/, data/, plus a START HERE note (2026-09-23). Edits in Obsidian change the project files. Renaming or moving those project files breaks the links.

## Booking and email (confirmed 2026-09-22)
- Booking calendar, notification recipient and Zoho sending address: ioseb@useprofitlens.com.
- Calls bookable all 7 days, 19:00 to 03:00 Georgia time (Asia/Tbilisi, no daylight saving).
- Chat model: Claude Sonnet 5 (ADR 0016, 2026-09-24; was Haiku 4.5).

## Accounts (credentials never written here)
- Anthropic API: account on platform.claude.com under profitlenstemplate@gmail.com (set up by a founder, 2026-09-24). $10 prepaid credit, auto reload OFF (founder's instruction: do not turn it on). Key name soso-chatbot, no expiry, lives only in .env.
- Google Calendar (service account): pending.
- Zoho Mail SMTP, EU servers (.zoho.eu): pending.
- Render: web service profitlens-chat at https://profitlens-chat.onrender.com (Virginia, Free plan for the hidden test page, deploys from GitHub soso357/profitlens-chatbot- branch master). Google sign-in file is a Render secret file at /etc/secrets/google-token.json.
