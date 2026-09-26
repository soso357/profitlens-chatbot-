# ADR 0020: Deploy through pull requests, with stage labels on commits and evals before review

- Status: Accepted
- Date: 2026-09-26
- Decided by: Ioseb (option A, full pull request flow)

## Context

An audit against the loop Plan (intent.md), Design (spec.md), Build (plan.md + code), Test (tests + evals), Deploy (PR + review), Maintain (new intent.md), with git as the audit trail, found: all 57 commits went straight to master (Render deploys master), no recorded review, only 19 of 57 commit messages named a phase, rule or ADR, test conversations had no automatic verdict, and intent.md had not changed since 22 Sep.

Options for Deploy:
- A. Full pull request flow: one branch per phase, a GitHub pull request, /code-review against REVIEW.md, Ioseb approves by merging. Pros: matches the loop, a permanent review record, nothing unreviewed reaches Render. Cons: one extra click per phase; Claude must never push master.
- B. Lighter: no pull requests, /code-review before each phase gate, report saved in docs/reviews/. Pros: simpler. Cons: less like the loop; review is not tied to what deploys.

## Decision

Option A. Work happens on a branch (`phase-N-short-name`, or `maintain-short-name` for setup work). Before asking for approval Claude runs `.venv/bin/python -m tests.evals` and `/code-review`, fixes Important findings, pushes the branch and opens a pull request whose description is the phase gate demonstration. Ioseb's approval is clicking Merge on GitHub; Render then deploys master.

Enforced in code, not only in instructions:
- `.githooks/commit-msg`: every commit starts with a stage label, `[Plan]`, `[Design]`, `[Build P5]`, `[Test P5]`, `[Deploy P5]` or `[Maintain]`.
- `.githooks/pre-push`: refuses a push to master (emergency override only with Ioseb's say-so).
- `.claude/settings.json` denies `--no-verify`, so Claude cannot skip the hooks.
- `tests/evals.py`: one command, all offline checks plus every scripted conversation with a pass or fail verdict (Must, Must not, Ends in lines in tests/conversations.md).
- Maintain: the phase-gate skill asks whether intent.md changed; intent.md keeps a dated change history, which starts the next loop.

## Consequences

Easier: every change on master has a review and an eval report behind it; `git log` shows which stage each commit belongs to. Harder: one click per phase for Ioseb; a new clone must run `git config core.hooksPath .githooks` once. Cost: an eval run uses a little API credit (about 35 chat replies). GitHub cannot enforce the rule on its side for a private repo on the free plan, so the local hook is the guard.
