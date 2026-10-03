# ProfitLens website chat agent

An AI chat widget for useprofitlens.com (done for you food cost analysis for independent US restaurants). It answers only from founder approved answers, asks qualifying questions, books the intake call in Google Calendar, and hands everything else to a founder by email. It never sells, negotiates, quotes figures, takes payment or gives advice.

## Working with Ioseb

Ioseb leads marketing, runs this build for the founders (Sophie, Leli, Tamuna), and is not a software engineer.
- Explain every technical term the first time, in one plain sentence. Reuse or extend memory/semantic/glossary.md.
- When choosing between approaches, give two or three options with plain pros and cons and wait. Never make a design decision silently. Record the choice (skill: new-adr).
- Phase gate: when a phase is done, run the evals and /code-review, open a pull request that demonstrates it and lists what you could not do and why, then stop. Ioseb approves by merging (skill: phase-gate, ADR 0020).

## Where things are (read only what the task needs)

| Need | File |
|---|---|
| Why we build this | docs/intent.md |
| What the chatbot must do: rules R1 to R14, behaviours B, code guardrails G | docs/spec.md |
| Where the project stands now: phase status, done, open questions | docs/progress.md |
| Phases and per phase plans | docs/plan.md |
| Decisions and why (founder decisions 0001 to 0006 are not reopened without a founder) | docs/adr/ |
| Event log | docs/build-log.md |
| What the chatbot knows (founders own it) | content/ |
| How we work: SDLC loop, context handoff, capability evolution | docs/workflow.md |
| Memory layers and search | memory/README.md |
| Review checklist | REVIEW.md |
| The founders' original brief (history, do not edit) | profitlens-chat-agent-full-prompt-with-architecture.md |

## Hard rules for you

1. The chatbot's rules R1 to R14 in docs/spec.md override convenience. Any rule on what the chatbot says is enforced in code, not only in its prompt.
2. No em dash or en dash in content/, UI text, or anything the chatbot says (a hook checks).
3. Secrets only in environment variables. Never read or print .env or credential files. New libraries need approval.
4. Before writing code in a phase, add a short plan to docs/plan.md "Phase notes" and get it approved.
5. Test with at least ten realistic visitor conversations per phase, including rude, off topic and trick questions.
6. Log every decision as one line in docs/build-log.md (not in this file); design choices also get an ADR. Update docs/progress.md when a phase or task moves.
7. Another Claude session may be working in this repo. Re-read shared files right before editing them. Stage files by name, never `git add -A`.
8. Same mistake twice: add it to memory/procedural/lessons.md and propose a rule.
9. Work on a branch, never master. Every commit message starts with its stage: `[Plan]`, `[Design]`, `[Build P5]`, `[Test P5]`, `[Deploy P5]` or `[Maintain]` (git hooks enforce both; never use --no-verify).

## Commands

```
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload            # run the chat service locally
.venv/bin/python -m tests.evals                    # all checks + scripted conversations, pass/fail (before every PR)
.venv/bin/python -m tests.evals --offline          # same without API calls
git config core.hooksPath .githooks                # once per clone: commit label and no-push-to-master hooks
python3 .claude/scripts/lint_content.py --all      # dashes and percentages in chatbot text
```

## Sessions and memory (automatic, see docs/workflow.md)

- Start: nothing is loaded. When Ioseb says "resume" (skill: resume), list open tasks, he picks one, load its handoff and docs/progress.md (ADR 0022).
- One session, one task, one type (Plan, Build, Fix, Content). Each task has its own handoff in memory/working/handoffs/ (skill: handoff). A parallel task gets its own worktree (skill: parallel-task).
- 60% context: update the task handoff. 70%: finish the step, hand off, commit, ask Ioseb for a new terminal (soft stop). Compaction at 85% is only a safety net.
- Fix sessions write an incident note with a required test (memory/incidents/).
- End: update the task handoff and docs/progress.md by hand (skill: handoff). No automatic summaries (ADR 0030).

## Compact instructions

When compacting, keep: the current phase and its gate status, every decision Ioseb made this session and the option chosen, questions still waiting for him, files changed, the branch and pull request in progress, and the exact next step. Drop tool output, file dumps and research already saved in docs/. This session's task handoff in memory/working/handoffs/, if updated in the last hour, is authoritative.

## Improving the setup

When you notice something useful Ioseb did not ask for (a repeated task, a spec gap, a missing guardrail or test), record it with the propose-capability skill and mention it in one sentence. Build only what Ioseb approves.
