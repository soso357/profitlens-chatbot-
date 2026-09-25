# ADR 0017: Haiku 4.5 while testing, Sonnet 5 for real visitors

- Status: Withdrawn 2026-09-25 (Ioseb chose to test on Sonnet too, so testers see what real visitors get)
- Date: 2026-09-25
- Decided by: Ioseb

## Context

ADR 0016 chose Claude Sonnet 5 for the website chat. During the hidden test page period many test conversations are run, and Ioseb wants them cheaper.

## Decision

While testing (hidden test page, local runs), CLAUDE_MODEL=claude-haiku-4-5, locally and in Render. Before the widget goes on the homepage, CLAUDE_MODEL is set back to claude-sonnet-5 in Render (ADR 0016 stays the choice for real visitors). The code default stays claude-sonnet-5.

## Consequences

About $0.03 per test conversation instead of about $0.05. Test results on Haiku are slightly weaker at booking (several answers in one message), so booking should get one final check on Sonnet before launch. The go live checklist in docs/plan.md includes switching the model back.
