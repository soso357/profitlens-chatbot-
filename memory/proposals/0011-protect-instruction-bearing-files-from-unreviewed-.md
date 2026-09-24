---
title: Protect instruction-bearing files from unreviewed Obsidian edits
status: proposed
kind: hook
source: 2026-09-23-919cea64.md
created: 2026-09-23
---

## Why
This session noted that editing a note in Obsidian changes the real project file, and told Ioseb to ask first before editing anything other than chatbot content, but nothing enforces that.

## What
A pre-commit or file-watch check that flags changes to CLAUDE.md, rules, or skills files if they were modified outside of a Claude Code session (e.g. via Obsidian) before they get committed.

## Decision
(pending Ioseb)
