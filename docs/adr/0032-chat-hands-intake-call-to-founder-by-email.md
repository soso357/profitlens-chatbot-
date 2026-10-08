# ADR 0032: The chat no longer books calls; a founder emails the visitor to set up the call

- Status: Accepted
- Date: 2026-10-08
- Decided by: Founders (approved, relayed by Ioseb on 2026-10-08). Option A of the remove-booking task.
- Links: supersedes ADR 0003; changes B4, B6, B11, B13 (spec 1.7), R10 (stack)

## Context

ADR 0003 asked the chat to book the intake call directly in Google Calendar, with time buttons and a fallback when the calendar fails (B6, B11). Two options were on the table:

- A. Remove the time buttons and the calendar booking. After name, restaurant, state and email, the chat says a founder will email them to set up the call. Founders get the same Telegram and email alert as today. Pros: far less code, no calendar failure path, no Google service account needed for booking. Cons: visitors cannot pick a time in the chat, and a founder must send each invite.
- B. Keep booking as built. Pros: no change for visitors. Cons: more code and a calendar dependency to keep working.

## Decision

Option A. The chat collects the four details (name, restaurant, state, email), then hands the visit to a founder by email, the same way as any other handoff. The founders alert (Telegram and email) includes the details and the chat. Founders email the visitor to set up the call. The chat never shows times and never books.

## Consequences

- Easier: less code, no time zones, no calendar outages, no Google Calendar scope needed for the chat.
- Harder: founders must send each call invite by hand, and visitors wait for an email instead of picking a time.
- The Google sign-in stays, because the founder alert emails still use it.
- Calendar settings (BOOKING_* and CALL_MINUTES) are removed from the service.
