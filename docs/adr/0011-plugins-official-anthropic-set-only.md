# ADR 0011: Plugins: official Anthropic set only

- Status: Accepted
- Date: 2026-09-22
- Decided by: Ioseb

## Context

40 plugin and skill repos from the AI Pulse Georgia list were inspected at code level (docs/research/2026-09-22-plugin-survey.md). The large frameworks (ECC, oh-my-claudecode, GSD, BMAD, spec-kit) install dozens of hooks and commands and would compete with this project's own memory and workflow.

## Decision

Install at project scope: skill-creator, claude-md-management, security-guidance, pyright-lsp (from anthropics/claude-plugins-official). Borrow ideas, not code, from the others. Any new third party skill is scanned (for example with NVIDIA SkillSpector --no-llm) and approved before install.

## Consequences

security-guidance runs a background LLM security review after replies and on commits (small token cost) and creates a venv under ~/.claude/security. pyright-lsp needed pyright installed globally (npm i -g pyright).
