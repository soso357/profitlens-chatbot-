# ADR 0028: Trim workflow overhead before the launch

- Status: Accepted, partly superseded by 0030
- Date: 2026-09-27
- Decided by: Ioseb (his written brief: trim overhead, keep the real gates)

## Context

Product work is done except the Phase 5 launch, but the process around it had grown: 35 proposals (15 open), an Obsidian map rebuilt at every session start, a context graph check in every eval run, 14 old branches and no worktrees. Keeping the process running was costing more than the product work.

## Decision

1. Open proposals are capped below 8 and only Phase 5 launch blockers stay open (0014, 0015, 0024, 0025, 0032, 0033). The rest are rejected or deferred with the reason in each file.
2. The Obsidian map rebuild is off by default: session_start.py runs obsidian_map.py only when PROFITLENS_OBSIDIAN=1.
3. The context graph check (tests.check_graph) is off by default: `tests.evals --graph` runs it. It guards links between documents, not what the chatbot does. The scripts are kept, not deleted.
4. The real gates stay in every run and on GitHub: gitleaks (secret scan), ruff (lint), pyright (type check), the spec check, the offline evals and pip-audit.
5. One worktree per open task (skill: parallel-task). The main folder is only for Maintain work, resume and memory.

## Consequences

Faster session starts and eval runs, a short proposal list. A broken link between a rule, its ADR and its code is no longer caught automatically; run `tests.evals --graph` before a phase gate if that matters. Switching either job back on is one environment variable or one flag.
