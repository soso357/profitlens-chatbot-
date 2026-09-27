# ADR 0026: Public repository, merges need green checks

- Status: Accepted
- Date: 2026-09-27
- Decided by: Ioseb (option: make the repository public)

## Context

GitHub blocks merging on red checks (a branch ruleset) only on paid plans or public repositories. Options: leave it (checks visible, not enforced, free); GitHub Pro ($4 a month, private, enforced); make the repository public (free, enforced). Claude advised Pro or leaving it, because a public repository shows the founders' approved answers and original brief, the chatbot's instructions and guardrails, email addresses and internal notes; the founders own content/. No secrets or visitor data were ever committed (full history secret scan clean, 2026-09-26).

## Decision

The repository is public (Ioseb, 2026-09-27). A branch ruleset on master is active: the "checks" job must pass before merging; deleting master and force pushing are blocked.

## Consequences

Mechanical gates are enforced for free. Anyone can read the project, including how Jelena's guardrails work, so guardrails must hold even when an attacker knows them (they are enforced in code, R1 to R4, R8). Nothing secret or about visitors may ever be committed (gitleaks runs on every pull request). The founders should be told the repository is public.
