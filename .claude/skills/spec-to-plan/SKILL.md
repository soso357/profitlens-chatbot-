---
name: spec-to-plan
description: The fixed path from an idea or request to an approved phase plan for the chatbot (context, intent, requirement, spec, Ioseb's approval, phase note). Use before planning any new chatbot phase or feature, when a request changes what the chatbot does, or when Ioseb asks to plan a phase (ADR 0025).
---

# Spec to plan (ADR 0025)

Flow: context, intent, requirements, spec, Ioseb's approval, plan, build. Never skip a step; planning works only from an approved spec, never from the conversation.

1. **Context and intent.** Read docs/intent.md. If the request changes why or for whom we build, propose the intent change first (Ioseb approves; add a line to its Change history).
2. **Requirements.** Write each new or changed requirement as a stable id in docs/spec.md (R for rules, B for behaviours, G for guardrails in code). Never renumber; retire with "RETIRED date". Anything the founders must decide is marked FOUNDER TO CONFIRM and cannot be planned.
3. **Acceptance.** Every id gets a row in section 8: the test that will prove it, "manual: how", or "none yet". Run `python3 .claude/scripts/spec_check.py`.
4. **Approval.** Any change to an approved spec makes it Draft (a hook compares a fingerprint of the text). Show Ioseb the changes in plain words and ask for approval. Only after he says approved, run `python3 .claude/scripts/spec_check.py approve` (sets the next version, Approved, the date and the fingerprint) and add a build-log line. Never approve on your own and never write `Status: Approved` by hand (the hook would undo it).
5. **Readiness.** `python3 .claude/scripts/spec_check.py ready <ids the phase covers>` must print ALL CHECKS PASSED.
6. **Phase note.** In docs/plan.md "Phase notes", heading `### Phase N name (YYYY-MM-DD)`, first line `Spec version X, covers R.., B.., G..`, then files touched, order and tests. Ask Ioseb to approve the note (CLAUDE.md rule 4).
7. **Build.** When an id with "none yet" is built, replace it with the test that proves it.
