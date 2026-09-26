# ADR 0025: Spec versions and approval before planning

- Status: Accepted
- Date: 2026-09-26
- Decided by: Ioseb (approved the foundation v2 step 4 plan note)

## Context

docs/spec.md had no version or approval status, so a phase could be planned from a spec that was still changing, or from conversation alone. Requirements had no stated proof; several (rate limit, spend cap, kill switch, allowed websites) had no test at all, and nothing showed it.

## Decision

The spec carries Version, Status (Draft or Approved), Approved by and Date. Any edit to an Approved spec sets it back to Draft (a PostToolUse hook), until Ioseb approves the next version. Section 8 names the check for every R, B and G id: a test, "manual: how", or "none yet". tests/check_spec.py fails when an id has no row or a named test does not exist, and when a phase note dated 2026-09-27 or later does not start with "Spec version X, covers ..." for the approved version, or covers an id that is FOUNDER TO CONFIRM. The skill spec-to-plan holds the steps.

## Consequences

Planning always starts from an approved, versioned spec. Gaps in testing are visible ("none yet") instead of hidden. Ioseb approves the spec more often, in small versions.
