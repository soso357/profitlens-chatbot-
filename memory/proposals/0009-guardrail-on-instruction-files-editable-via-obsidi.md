---
title: Guardrail on instruction files editable via Obsidian
status: rejected
kind: rule
source: 2026-09-23-919cea64.md
created: 2026-09-23
---

## Why
CLAUDE.md, rules, and skills are now live-linked into Obsidian and editable there, but Claude Code treats them as trusted instructions with no check that an edit came from a reviewed source.

## What
A rule or checksum step that flags CLAUDE.md/rules/skills files if they were modified outside a Claude Code session, so an Obsidian edit gets reviewed before being treated as authoritative.

## Decision
Ioseb, 2026-09-26 (proposal review): rejected. Every change now reaches master through a pull request Ioseb reads (ADR 0020). Same idea as 0010 and 0011.
