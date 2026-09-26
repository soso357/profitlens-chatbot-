# ADR 0025: Spec versions and approval before planning

- Status: Accepted
- Date: 2026-09-26
- Decided by: Ioseb (approved the foundation v2 step 4 plan note)

## Context

docs/spec.md had no version or approval status, so a phase could be planned from a spec that was still changing, or from conversation alone. Requirements had no stated proof; several (rate limit, spend cap, kill switch, allowed websites) had no test at all, and nothing showed it.

## Decision

The spec carries Version, Status (Draft or Approved), Approved by, Date and a Fingerprint (a short hash of its text). Only `spec_check.py approve`, run after Ioseb says approved, sets Approved and the fingerprint. If the text later changes by any tool, a PostToolUse hook sets it back to Draft, and the evals fail on an Approved spec whose fingerprint does not match. Section 8 names the check for every R, B and G id: a test, "manual: how", or "none yet". tests/check_spec.py fails when an id has no row or a named test does not exist, and when a phase note (other than the four tagged [before spec versions]) does not start with "Spec version X, covers ..." for the approved version, or covers an id blocked by a FOUNDER TO CONFIRM item. Such items name the ids they block. The skill spec-to-plan holds the steps.

## Consequences

Planning always starts from an approved, versioned spec. Gaps in testing are visible ("none yet") instead of hidden. Ioseb approves the spec more often, in small versions.
