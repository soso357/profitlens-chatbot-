# Foundation v2: design for review

Status: APPROVED 2026-09-26 (Ioseb: all recommended options, ADR 0023). Built step by step, see section 9.
Date: 2026-09-26. Branch: maintain-foundation-v2.
Scope: upgrade this ProfitLens repo only (Ioseb, 2026-09-26). Not a reusable template.

This document covers the eight points of Ioseb's brief of 2026-09-26. Each section says what exists already, what changes, and any choice Ioseb must make (marked **CHOICE**). Section 9 is the build order. Principle throughout: design first, build in small steps, each step one pull request.

---

## 0. What exists today (so we do not rebuild it)

| Area | Already in place |
|---|---|
| Instructions | CLAUDE.md (one page), .claude/rules/, REVIEW.md |
| Artifact chain | docs/intent.md, docs/spec.md (R1 to R14, B, G ids), docs/plan.md, 21 ADRs, docs/build-log.md |
| Memory | 7 layers in memory/ (README), SQLite search index, recall skill |
| Sessions | automatic session summary at session end, start brief, handoff at 60%, compaction at 70%, stop after 3 |
| Self improvement | memory/proposals/ with proposed, approved, built lifecycle; propose-capability skill |
| Harness | permission deny list, git hooks (stage label, no push to master), content dash lint hook |
| Tests | tests/evals.py: offline checks plus 17 scripted conversations with pass or fail |
| Graph | Obsidian vault with live links to every file, one "START HERE" map |

---

## 1. Handoff protocol (from the interview)

Ioseb's answers, 2026-09-26 (ADR 0022):
- Session types: Plan, Build, Fix (live incident), Content and review.
- Works with several terminals at the same time.
- A new session starts clean. Context is loaded only when Ioseb says "resume".
- One handoff file per task or branch.
- Must always survive: decisions and why, open questions, exact next step, what failed and must not be redone.
- Start a new session when: the task is finished, the session type changes, or context reaches 70%.
- At 70%: hand off and open a fresh session. Compaction stays only as a safety net.
- Live incidents write a short incident note.
- Handoff is a fixed one page template.

### 1.1 Session types

| Type | Responsible for | Must write before ending |
|---|---|---|
| Plan | intent, spec, phase notes, options, ADRs | spec or plan changes, ADRs, open questions |
| Build | code and tests for one approved phase note, on one branch | handoff, commits, eval result |
| Fix | one live problem: find cause, fix, add a test | incident note (1.5), a new test case, a lesson |
| Content and review | founder answer changes, proposal reviews, transcript reading | content change log line, proposal statuses |

Rule: one session, one type, one task. If the type changes, Claude says so and offers a handoff.

### 1.2 Files

```
memory/working/handoffs/<task-slug>.md     one per task or branch (replaces the single handoff.md)
memory/working/handoffs/_index.md          generated list: task, type, branch, updated, status (open or done)
memory/incidents/YYYY-MM-DD-<slug>.md      incident notes (in git, never visitor data)
```

### 1.3 The template (always the same sections, one page)

```
# Handoff: <task>
Type: Plan | Build | Fix | Content
Branch: <branch>   Worktree: <folder>   Updated: YYYY-MM-DD HH:MM   Status: open | done

## Goal            one or two lines, Ioseb's words
## State           what works now and how it was verified; what is half done
## Decisions       decision, option chosen, by whom, ADR number
## Open questions  for Ioseb / for founders, each with who must answer
## Next step       the single next action, then the one after
## Do not redo     what failed and why; research already saved (paths only)
## Files           path: what changed (uncommitted marked *)
```

Not carried forward: tool output, file contents, exploration that led nowhere without a lesson, anything already in docs/ (link it instead), any visitor data or secret.

### 1.4 Triggers

| When | What happens |
|---|---|
| Session start | Nothing is loaded. The start hook adds one line: "Say resume to continue a task." |
| Ioseb says "resume" | Claude lists open handoffs (task, type, age). Ioseb picks. Claude reads that handoff, progress.md and the files it names, then states in three lines where it is. |
| 60% context | Claude writes or updates the handoff for its task. |
| 70% context | Claude finishes the current small step, updates the handoff, commits, and tells Ioseb to open a new terminal. **CHOICE C3**: soft (Claude is told to stop, Ioseb can override) or hard (a hook refuses new work prompts except "handoff"). Recommended: soft. |
| About 85% | Automatic compaction as a safety net only (setting moves from 70 to 85). |
| Task finished | handoff Status: done; progress.md updated; Claude suggests a new session for the next task. |
| Type changes | Claude says "this is now a Fix session", writes the handoff for the old task, suggests a new terminal. |
| Full reset (/clear) | When a session read wrong information, got confused, or after a phase gate. The next session rebuilds only from files. |

### 1.5 Incident note (Fix sessions)

```
# Incident YYYY-MM-DD: <what visitors or founders saw>
What broke / When found, by whom / Cause / Fix (commit or PR) / Test added / Lesson / Still open
```
The test added is required. The lesson goes to memory/procedural/lessons.md automatically.

### 1.6 Preventing drift between sessions

1. Files are the truth, conversations are not. A new session reads files, never older summaries first.
2. Precedence when two sources disagree (Ioseb, 2026-09-26): founder ADRs 0001 to 0006, then spec.md, then other ADRs, then plan.md, then progress.md, then lessons, then session summaries, then handoffs. Claude uses the higher one and flags the lower one to be fixed.
3. Handoffs record the git commit they were written at. On resume, Claude checks what changed since (other terminals) before continuing.
4. Parallel terminals each work in their own worktree. **CHOICE C2**: a git worktree is a second copy of the project folder on its own branch, so two terminals never switch each other's branch or overwrite each other's files. Option A (recommended): one worktree per parallel task, created by a skill. Option B: keep one folder and be careful (today's setup, has caused clashes).

---

## 2. Context engineering

### 2.1 New file: docs/progress.md

What is true right now, updated continuously. **CHOICE C1**: move the phase status table from plan.md into progress.md so status lives in one place (recommended), or keep it in plan.md and have progress.md only for "recent changes and open questions".

Sections: Current phase and gate / Done (dated, newest first, one line each, links to PRs) / In progress (links to open handoffs) / Open questions (single home for them, with owner) / Waiting on people (founders, Ioseb) / Known problems.

plan.md keeps the phases and phase notes (how we will build). build-log.md keeps the decision log.

### 2.2 Session summary distribution

Today the summarizer only saves a file. New: it outputs routed items, and a distributor script sends each to its home.

| Item from a summary | Goes to | Approval |
|---|---|---|
| Work done | progress.md "Done" | automatic |
| Open question | progress.md "Open questions" | automatic |
| Waiting on a person | progress.md | automatic |
| A decision Ioseb made | checked against build-log.md and ADRs; if missing, a proposal to record it | Ioseb |
| Mistake made | lessons.md (twice: a rule proposal) | automatic for the lesson, Ioseb for the rule |
| Plan, spec, ADR or rule change | memory/proposals/ | Ioseb |
| New capability idea | memory/proposals/ | Ioseb |

Every automatic write is one line with a link back to the session summary, so any wrong line can be traced and removed. The summary itself stays in memory/episodic/ as the record.

### 2.3 Orientation without repeating yourself

Three levels, loaded in this order and only as needed:
1. Always loaded: CLAUDE.md (one page) and .claude/rules/.
2. On "resume": the chosen handoff, progress.md, and files the handoff names.
3. On demand: search (recall skill) over memory, docs and the graph (section 3).

---

## 3. Context graph (Obsidian)

Today every file links to one START HERE page. That makes a star shape, which looks full but tells nobody how things relate.

Goal: real, typed links. Example: rule R2 "no figures" links to ADR 0004 (why), to G-guardrail code in app/guardrails.py (how), to tests that check it, and to incidents where it failed.

**CHOICE C4:**

| Option | How | Pros | Cons |
|---|---|---|---|
| A (recommended) | Each note gets a small header (frontmatter: a few labelled lines at the top of a file) with typed links: implements, decided_by, tested_by, supersedes. A script builds the graph into the existing SQLite index; Obsidian shows the same links. Claude asks the index "what depends on R2?" | Useful for Claude and for Ioseb; standard library only; no new tools | Headers must be kept up to date (a check does it) |
| B | Obsidian only, links written by hand | Simple | Only visual; Claude gets no benefit |
| C | A graph database or a third party memory server | Powerful queries | New software to install and review (ADR 0011), more to maintain, overkill for one repo |

With A, a check fails if a requirement has no test, a decision has no reason, or a link points to nothing. That turns the graph into a quality gate, not a picture.

---

## 4. Memory architecture

Mapping of the layers Ioseb listed to where they live. No new folders except incidents and handoffs.

| Layer | Holds | Where | Written when | Read when | Goes stale how |
|---|---|---|---|---|---|
| Working / session | the current task | memory/working/handoffs/ | 60%, 70%, end of task | on resume | Status: done after the task; deleted after 14 days done |
| Episodic | what happened | memory/episodic/sessions/, memory/incidents/ | session end (automatic), incidents | search only | never edited; lowest precedence |
| Project | current state | docs/progress.md, docs/plan.md | continuously (2.2) | on resume | overwritten, not appended (except Done list) |
| Semantic | facts that are true | docs/intent.md, docs/spec.md, memory/semantic/, content/ | when Ioseb or a founder confirms | on demand | each file has "last verified: date"; older than 60 days flagged when read |
| Decision | why | docs/adr/, docs/build-log.md | when Ioseb chooses | on demand, and before re-deciding anything | never edited; replaced by a new ADR |
| Procedural | how we work | CLAUDE.md, rules, skills, lessons.md | after approval | always (CLAUDE.md, rules), skills when triggered | reviewed at each phase gate |
| Prospective | ideas | memory/proposals/ | during work and by the summarizer | at resume, at natural pauses | deferred ones re-asked after 30 days |
| Personal | how Ioseb likes to work | Claude's own auto memory | Claude Code | automatically | corrected when Ioseb corrects |

Conflicts follow the precedence order in 1.6. A memory found wrong is fixed or deleted, never left next to the right one (existing rule).

---

## 5. Agent harness (what Claude may do)

Today there is only a deny list. New: three lists plus a guard script.

| Level | Examples |
|---|---|
| Allowed without asking | read project files (not secrets); edit docs/, memory/, app/, tests/, .claude/ on a branch; run tests, evals, lint; git status, diff, log, add by name, commit on a branch |
| Ask Ioseb first | git push; opening a pull request; installing any library; editing content/ (founder owned); editing CLAUDE.md, settings.json or hooks; any command that talks to the live site, Telegram, Gmail, Calendar or the Anthropic API; deleting files |
| Never | read or print .env, secrets/ or credential files; push to master; merge a pull request; force push; hard reset; skip git hooks; change Render settings or billing; delete data/, logs/ or leads; send anything to a visitor or founder outside a test |

How it is enforced:
1. settings.json permissions with allow, ask and deny lists.
2. A PreToolUse hook (runs before every tool use) that refuses writes outside the project and outside the allowed folders, and refuses commits on master.
3. Claude Code sandboxing (limits what shell commands can touch on disk and on the network) for commands; tested before switching on, since the evals call the network.
4. Git hooks as today.
5. A test (tests/check_harness.py) that tries each "never" action and confirms it is refused.

Human approval points stay: phase note approval, spec approval, pull request merge, founder approval before launch.

---

## 6. Specification driven development

Flow: Context, then Intent, then Requirements, then Spec, then Ioseb's approval, then Plan, then Build.

Changes:
1. spec.md gets a header: Version (1.0, 1.1...), Status (Draft or Approved), Approved by, Date. Any edit to an approved spec makes it Draft again until Ioseb approves.
2. Each requirement gets an acceptance check line: how we know it works (which test).
3. A readiness check (script) before planning: every requirement in the phase has an id and an acceptance check, none is FOUNDER TO CONFIRM, the spec is Approved.
4. Each phase note in plan.md starts with "Spec version X, covers R.., B.., G..". A check fails if the version is not the approved one.
5. The flow is written as one skill (spec-to-plan) so every phase goes through the same steps.

---

## 7. Future multi model orchestration (designed now, OFF)

Two loops, each with a hard limit:

```
Architecture decision (once per decision):
  Maker (Claude Fable 5.1) writes proposal
    -> Checker (OpenAI model, Ioseb's "Astra") audits it
    -> Maker writes final synthesis -> Ioseb approves -> ADR

Coding (max 2 rounds):
  Coder (Claude Opus 5.5) writes the change on a branch
    -> Reviewer (OpenAI model, Ioseb's "Sol") reviews the diff against the spec
    -> Coder fixes -> Reviewer checks again -> stop, whatever the result; open items go to Ioseb
```

Note: I cannot confirm the OpenAI model names "Astra" and "Sol" from my own knowledge (cut off June 2026). They are settings, filled in when the loop is switched on. Claude Opus 5.5 is the current Opus.

Design:
- orchestration/config.yaml: enabled: false, model per role, loop limits, spend cap per run.
- orchestration/run.py: reads the config, refuses to run while disabled.
- Every run saves its inputs and outputs to docs/reviews/ so it can be audited.
- Mechanical gates (section 8) run before any model review; a model never reviews code that fails a mechanical check.

Access control for the outside model, in stages (Ioseb switches each stage on):

| Stage | The outside model can | Cannot |
|---|---|---|
| 0 (now) | nothing | anything |
| 1 | read text Ioseb or the script sends it (a proposal, a diff, the spec) and answer | see the repo, secrets, visitor data; run commands; write files |
| 2 | same, sent automatically by run.py | same |
| 3 | comment on a pull request | merge, push, write to the repo |

Its API key lives only in an environment variable. It never receives .env, content of data/ or logs/, or visitor information.

**CHOICE C6**: build the disabled scaffold now (config, runner that refuses, docs), or write only this design and build the scaffold when switched on. Recommended: design only now, since the model names are not known and nothing uses it yet.

---

## 8. Automated tests and gates

Rule: anything that can be checked mechanically is checked mechanically, not by a model.

Introduced in levels. Each level is added when useful, not all at once.

| Level | When | Gates | New tools (need approval, development only, not in the live service) |
|---|---|---|---|
| 1 | now | existing evals; lint (automatic check for errors and messy code); type check (checks that values are the kind of thing the code expects); unit tests for guardrails; secret scan of each commit | ruff (lint), pytest (tests); pyright is already installed as a plugin |
| 2 | with this upgrade | CI: GitHub runs level 1 on every pull request and shows a red or green mark; dependency security audit | GitHub Actions (free), pip-audit |
| 3 | before homepage launch | visitor phrasing regression tests (proposal 0014), post deploy smoke check (0015), reply time check (performance), harness test (5) | none |
| 4 | after launch | incidents become tests; weekly transcript eval; model based judgement only for tone and helpfulness, which cannot be checked mechanically | none |

A pull request cannot be merged unless all mechanical gates are green (GitHub branch protection, which Ioseb switches on once).

**CHOICE C5**: approve the level 1 and 2 tools (ruff, pytest, pip-audit, GitHub Actions, a secret scanner).

---

## 9. Build order (each step one pull request, each needs Ioseb's approval to start)

| Step | What | Why this order |
|---|---|---|
| 1 | Handoff protocol, progress.md, resume, 70% stop, worktrees | used every session; fixes parallel terminal clashes |
| 2 | Summary distribution, memory staleness and precedence | keeps progress.md and memory current automatically |
| 3 | Harness: allow, ask, deny lists, guard hook, harness test | safety before more autonomy |
| 4 | Spec versioning, acceptance checks, readiness check, spec-to-plan skill | controls the start of the remaining Phase 5 work |
| 5 | Test gates levels 1 and 2, CI | needs tool approval |
| 6 | Context graph (option chosen in C4) | builds on the files from steps 1 to 4 |
| 7 | Orchestration scaffold (if C6 says build) | last; off until Ioseb switches it on |

Phase 5 launch items (Render Telegram ID, new API key, paid plan, deletion, kill switch, README, privacy text) continue in parallel in their own sessions. **CHOICE C7**: this order, or put launch items first.

---

## Choices waiting for Ioseb

| Id | Question | Recommended |
|---|---|---|
| C1 | Phase status table moves to progress.md? | yes |
| C2 | One git worktree per parallel task? | yes |
| C3 | 70% stop soft or hard? | soft |
| C4 | Context graph option | A |
| C5 | Approve ruff, pytest, pip-audit, GitHub Actions, secret scanner | yes |
| C6 | Orchestration: design only now, or scaffold now | design only |
| C7 | Build order as in section 9, or launch items first | section 9 order, launch items in parallel |
