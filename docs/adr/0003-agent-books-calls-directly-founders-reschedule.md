# ADR 0003: Agent books calls directly; founders reschedule

- Status: Accepted
- Date: 2026-09 (founder brief)
- Decided by: Founders

## Context

Booking friction loses leads, but rescheduling involves judgment and founder availability.

## Decision

The agent books the intake call directly in Google Calendar (service account, Meet link, visitor's US time zone) and notifies a founder. Rescheduling is done by a founder by email reply.

## Consequences

Needs a Google Cloud service account with 'make changes to events' access. Calendar failure must fall back to email handoff (spec B11).
