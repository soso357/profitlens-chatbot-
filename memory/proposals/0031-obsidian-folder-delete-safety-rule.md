---
title: Obsidian folder-delete safety rule
status: rejected
kind: rule
source: 2026-09-27-170044-d2856c37.md
created: 2026-09-27
---

## Why
Ioseb deleted the entire Obsidian project shortcut folder instead of a single note, breaking links to all 155 project files (recovered, no real data lost)

## What
Add a rule/reminder that Claude explicitly flags the difference between deleting a single note versus a folder in the vault before suggesting either

## Decision
Ioseb, 2026-09-27 (trim workflow overhead, ADR 0028): rejected. Obsidian map rebuild is switched off by default (ADR 0028).
