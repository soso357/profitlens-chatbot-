# ADR 0012: Context handoff, compaction and session limits

- Status: Superseded by 0022
- Date: 2026-09-22
- Decided by: Ioseb

## Context

Long sessions degrade: after several compactions the agent works from summaries of summaries. Ioseb asked for a handoff at 60 to 70 percent context, compaction, and a clear signal after 3 to 4 compactions.

## Decision

At 60 percent context a hook tells Claude to write memory/working/handoff.md (skill: handoff). Auto compaction triggers at 70 percent (CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70). After compaction a hook reinjects the handoff and increments a per session counter. The statusline shows context use and the counter; at 3 compactions it turns red and says to open a new terminal or /clear.

## Consequences

The percentage the statusline sees lags one turn. The handoff is written by Claude, so a hook also saves a mechanical snapshot before every compaction as a fallback.
