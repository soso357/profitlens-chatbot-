---
title: Guardrail on instruction files editable via Obsidian
status: proposed
kind: rule
source: 2026-09-23-919cea64.md
created: 2026-09-23
---

## Why
CLAUDE.md, rules, and skills are now live-linked into Obsidian and editable there, but Claude Code treats them as trusted instructions with no check that an edit came from a reviewed source.

## What
A rule or checksum step that flags CLAUDE.md/rules/skills files if they were modified outside a Claude Code session, so an Obsidian edit gets reviewed before being treated as authoritative.

## Decision
(pending Ioseb)
