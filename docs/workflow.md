# Development workflow

How Ioseb and Claude Code build this project. Based on Anthropic's AI native SDLC playbook (ADR 0008), sized for one non engineer, one repo and one Claude Code user.
Principle from the playbook: every stage commits a file the next stage reads, and humans stay accountable for every decision that needs judgment.

## 1. The artifact chain

```
 intent.md  ->  spec.md  ->  plan.md (phase notes)  ->  code + tests  ->  phase gate  ->  deploy
 (why)          (what,       (how, file by file,        (tests/,          ("approved"    (Render,
                 R/B/G ids)   approved before code)      conversations)    from Ioseb)    founders)
      ^                                                                                     |
      |__________ proposals, incidents, transcript reviews, session summaries ______________|
```

| Stage | Claude does | Ioseb does | Artifact |
|---|---|---|---|
| Intent | Drafts from Ioseb's words | Approves | docs/intent.md |
| Spec | Turns intent into numbered requirements; flags open questions | Resolves questions with founders | docs/spec.md |
| Plan | Before each phase, writes a phase note: files, order, tests | Approves the note | docs/plan.md |
| Build | Implements in small steps, runs things, verifies | Answers questions, chooses options | code, docs/adr/, docs/build-log.md |
| Test | `tests.evals`: offline checks plus every scripted conversation with a pass or fail verdict | Tries rude and trick questions himself | tests/, tests/eval-report.md, transcripts |
| Gate | Demonstrates (skill: phase-gate), /code-review against REVIEW.md, opens a pull request | Reads the pull request | pull request on GitHub |
| Deploy | Never pushes master (a git hook refuses it) | Clicks Merge; Render deploys master. Founders approve the widget on the hidden test page | merged pull request, Render, Framer |
| Maintain | Asks at each gate whether intent changed; turns incidents into test conversations and proposals | Answers; founders read transcripts weekly for the first month | docs/intent.md change history, proposals, tests |

Git is the audit trail (ADR 0020): every commit message starts with its stage, `[Plan]`, `[Design]`, `[Build P5]`, `[Test P5]`, `[Deploy P5]` or `[Maintain]` (setup, memory and workflow work). A git hook refuses other messages, so `git log` shows which stage each change belongs to. Work happens on a branch (`phase-N-name` or `maintain-name`) and reaches master only through a merged pull request.

Source of truth for each thing is exactly one file (playbook rule): requirements in spec.md, status in plan.md, decisions in docs/adr/, chatbot knowledge in content/.

## 2. A normal session

1. Start `claude` in the project folder. The session start hook briefs Claude: plan status, last session's next steps, open proposals, any leftover handoff.
2. If the last summary is marked unreviewed, Claude skims it and fixes anything wrong.
3. Work. Every choice between approaches: two or three options, plain pros and cons, wait. Then an ADR (skill: new-adr).
4. At 60% context the statusline turns yellow and a hook asks Claude to write the handoff (skill: handoff). At 70% Claude Code compacts automatically and the handoff is reinjected. The counter goes up by one.
5. After 3 compactions the statusline turns red: "STOP: open a new terminal or /clear". Continue in a new terminal and say "continue from the handoff".
6. When you close the session, a background job writes the session summary to memory/episodic/sessions/ and any improvement ideas to memory/proposals/. Nothing to do by hand.
7. Commit on the branch when a step works, with a stage label. At the phase gate: evals, review, pull request, Ioseb merges.

## 3. Context handoff and compaction

| Context used | Statusline | What happens |
|---|---|---|
| under 60% | green bar | normal work |
| 60 to 69% | yellow "handoff" | hook injects: write memory/working/handoff.md now (once per cycle) |
| 70% | red "compacting" | auto compaction (CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70). PreCompact hook saves snapshot.md and tells the compactor what must survive |
| after compaction | "compactions n/3" | SessionStart(compact) hook reinjects handoff.md; counter +1; context counter effectively starts again |
| 3 compactions | red "STOP" | Claude tells you once to open a new terminal or /clear |

What must survive a compaction is written in the "Compact instructions" section of CLAUDE.md (Claude Code reads it when compacting). The PreCompact hook only saves the snapshot: Claude Code rejects extra context from that hook, as the first real compaction test (2026-09-26) showed. tests/check_workflow.py checks all of this offline.

Why 3: each compaction is a summary of a summary. By the third, early decisions survive only as paraphrase, and the files in docs/ and memory/ are a better starting point than the conversation.

Two kinds of ending:
- **New terminal**: keeps this terminal's history; the new session picks up from handoff.md and the latest summary.
- **/clear**: same terminal, empty context; the start hook briefs the fresh context the same way.

## 4. Capability evolution (self improvement)

Goal: Claude notices useful things Ioseb did not ask for, proposes them, and builds them only after approval.

Where ideas come from:
1. The session summarizer lists up to three proposals per session (automatic).
2. Claude during work (skill: propose-capability), triggered by: the same manual task done twice; a visitor situation the spec does not cover; a guardrail or test that is missing; a mistake made twice (lessons.md); a founder or Ioseb correction.
3. Incidents after launch: every bad transcript becomes a test case and, if needed, a proposal.

Lifecycle: `proposed -> approved -> built` (or rejected / deferred with a reason). Files in memory/proposals/.

Rules:
- Claude never builds an unapproved proposal and never installs third party code without a code review and approval (ADR 0011).
- Skills are built with the skill-creator plugin and at least two test prompts, then the proposal is set to built.
- A proposal of kind "rule" becomes a line in CLAUDE.md or .claude/rules/ only after approval; CLAUDE.md stays under one page (claude-md-management plugin: /revise-claude-md).
- Nothing may weaken a founder decision (ADR 0001 to 0006) or rules R1 to R14.
- Review cadence: open proposals are listed at every session start and in the statusline; decide them at a natural pause, not mid task. When more than 8 are waiting, the brief asks for a short review session.

## 5. Guardrails for Claude Code itself (hooks)

| Hook | Script | Does |
|---|---|---|
| SessionStart | session_start.py | brief at start; handoff reinjection and counter after compaction |
| UserPromptSubmit | context_guard.py | handoff nudge at 60%, session limit nudge |
| PreCompact | pre_compact.py | snapshot (the instructions are in CLAUDE.md) |
| PostToolUse (Write/Edit) | lint_content.py | blocks dashes and percentages in chatbot text |
| SessionEnd | session_end.py -> summarize_session.py | automatic session summary and proposals; one run per session at a time; a resumed session is summarized only from where the last summary ended; a failure shows in the statusline and the next session brief until redone |
| git commit-msg | .githooks/commit-msg | refuses a commit without a stage label |
| git pre-push | .githooks/pre-push | refuses a push to master (pull requests only) |
| permissions.deny | settings.json | Claude cannot read .env or credential files, no force push, no hard reset, no skipping git hooks |
| plugin security-guidance | (Anthropic) | security warnings on edits, background review of commits |

All project scripts are standard library Python in .claude/scripts/. The summarizer log is memory/working/state/summarizer.log.

## 6. Measures (from the playbook, scaled down)

- Rework: how often a phase is sent back after demo.
- Guardrail escapes: transcripts where a figure, promise, invented answer or dash reached a visitor (target: zero).
- Proposals: share approved and built vs rejected (too many rejections means Claude proposes noise).
