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

1. Start `claude` in the project folder (or in a task's worktree). Nothing is loaded (ADR 0022). Say **resume**: Claude lists the open tasks, you pick one, Claude reads its handoff and docs/progress.md, checks what other terminals committed since, and says in three lines where it is (skill: resume).
2. One session, one task, one type: Plan, Build, Fix (live incident) or Content and review. If the type changes, Claude writes the handoff and suggests a new terminal. For a second task at the same time, Claude sets up a worktree (skill: parallel-task).
3. If the last summary is marked unreviewed, Claude skims it and fixes anything wrong.
4. Work. Every choice between approaches: two or three options, plain pros and cons, wait. Then an ADR (skill: new-adr).
5. At 60% context the statusline turns yellow and Claude updates the task handoff. At 70% it turns red "new terminal": Claude finishes the step, hands off, commits and asks you to open a new terminal and say resume.
6. Fix sessions end with an incident note in memory/incidents/ and a new test.
7. When you close the session, a background job writes the session summary to memory/episodic/sessions/ and any improvement ideas to memory/proposals/. Nothing to do by hand.
8. Commit on the branch when a step works, with a stage label. At the phase gate: evals, review, pull request, Ioseb merges.

## 3. Context handoff and compaction

| Context used | Statusline | What happens |
|---|---|---|
| under 60% | green bar | normal work |
| 60 to 69% | yellow "handoff" | hook: update this task's handoff in memory/working/handoffs/ (once per cycle) |
| 70 to 84% | red "new terminal" | hook: soft stop (ADR 0023 C3): finish the step, hand off, commit, ask for a new terminal; you may say continue |
| 85% | | safety net: auto compaction (CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=85). PreCompact hook saves a per session snapshot |
| after compaction | red "compacted" | SessionStart(compact) hook reinjects this session's own task handoff (never another terminal's) and asks for a new terminal |

What must survive a compaction is written in the "Compact instructions" section of CLAUDE.md (Claude Code reads it when compacting). The PreCompact hook only saves the snapshot: Claude Code rejects extra context from that hook, as the first real compaction test (2026-09-26) showed. tests/check_workflow.py checks all of this offline.

Why a new session instead of compaction (ADR 0022): each compaction is a summary of a summary and early decisions survive only as paraphrase. The files in docs/ and the task handoff are a better starting point than the conversation.

Which task a session owns: the hook handoff_track.py records it when Claude writes a handoff; otherwise the open handoff on the same branch. Handoffs, snapshots and state always live in the main project folder, also for terminals in a worktree.

When sources disagree: founder ADRs 0001 to 0006, spec.md, other ADRs, plan.md, progress.md, lessons, session summaries, handoffs. The higher one wins; Claude flags the lower one.

Two kinds of ending:
- **New terminal**: keeps this terminal's history; say resume and pick the task.
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
| SessionStart | session_start.py | one line at start (nothing loaded until resume); after compaction: this task's handoff and a new terminal request |
| UserPromptSubmit | context_guard.py | handoff nudge at 60%, soft stop at 70%, new terminal after a compaction |
| PreCompact | pre_compact.py | snapshot (the instructions are in CLAUDE.md) |
| PostToolUse (Write/Edit) | lint_content.py | blocks dashes and percentages in chatbot text |
| PostToolUse (Write/Edit) | handoff_track.py | remembers which task this session owns; rebuilds the task index |
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
