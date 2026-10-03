---
name: propose-capability
description: Record an improvement idea (new skill, rule, hook, spec change, test or doc) in memory/proposals/ for Ioseb to approve. Use whenever you notice a repeated task, a gap in the chatbot spec, a missing guardrail or test, or a mistake made twice, even if nobody asked. Also use to approve, reject or mark a proposal built.
---

# Propose a capability

## New proposal
1. Check it is not already there: `grep -h "^title:\|^status:" memory/proposals/0*.md` (rejected and built ones are in git history: `git log --diff-filter=D --name-only -- memory/proposals`).
2. Create memory/proposals/NNNN-short-slug.md (next free number):

```
---
title: <one line>
status: proposed
kind: skill | rule | hook | spec | test | doc
source: <session date or file that revealed it>
created: YYYY-MM-DD
---

## Why
Evidence: what happened, how often, what it costs if we do nothing.

## What
What would be created or changed, where, and how we would test it.

## Decision
(pending Ioseb)
```

3. Tell Ioseb in one or two plain sentences and ask: approve, reject, or later. Do not build anything yet.

## Changing status
- approved: set `status: approved`, write the date and "approved by Ioseb" under Decision.
- rejected or deferred: set status, write the reason (so it is not proposed again).
- built: after building and testing, set `status: built` and list what was created (paths) under Decision. For skills, use the skill-creator plugin and include at least two test prompts.
