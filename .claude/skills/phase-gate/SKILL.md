---
name: phase-gate
description: End-of-phase demonstration checklist for the ProfitLens build (rules R12 and R13). Use when a build phase looks finished, before telling Ioseb it is done, or when Ioseb asks to demo a phase.
---

# Phase gate

Do not say a phase is done until every item is true.

0. Work happens on a branch (`phase-N-short-name`), never on master (ADR 0020). Commits start with a stage label, e.g. `[Build P5] Kill switch (R8)`; a git hook refuses others.
1. Re-read the phase's "Demonstrate" line in docs/plan.md. That is the acceptance test.
2. Run it for real (service started, requests sent, emails or calendar checked). Paste the actual output, not a description.
3. Run `.venv/bin/python -m tests.evals`: every offline check plus every scripted conversation with a verdict. All must pass (R13: at least ten realistic conversations for this phase, including rude, off topic and trick questions; add this phase's conversations to tests/conversations.md with Must and Must not lines first). A failing check is fixed in the code, not by loosening the check, unless the check itself is wrong; say which.
4. Check the guardrails relevant to this phase caught real violations (show at least one catch each).
5. Run `python3 .claude/scripts/lint_content.py --all` and confirm it prints OK (R4, R2).
6. Run `/code-review` against REVIEW.md. Fix every Important finding; list the Nits.
7. Maintain check: ask Ioseb one question, "Has anything changed in why we build this or for whom?" If yes, update docs/intent.md and add a dated line to its "Change history". If intent changed, check spec.md still follows from it.
8. Update the status table in docs/plan.md ("waiting for merge") and add a line to docs/build-log.md.
9. Push the branch and open a pull request (`gh pr create`). The description is the demonstration, in plain English: what works, how you verified it (eval score, review result), what you could not do and why, what you need from Ioseb or the founders.
10. Tell Ioseb the link. Stop. His approval is clicking Merge on GitHub (a plain "approved" in the chat also counts, then Claude merges with `gh pr merge --merge`). Render deploys master after the merge.
11. After the merge: `git switch master && git pull`, mark the phase approved in docs/plan.md in a `[Maintain]` commit on the next branch.
