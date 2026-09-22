---
paths:
  - "content/**"
  - "app/**"
  - "tests/**"
---

# Writing anything the chatbot reads, says or shows

Applies when editing content/, the system prompt, widget UI text, or scripted test conversations.

- Only the founders decide what the chatbot may say. Do not add facts, prices, timelines or promises to content/approved-answers.md; mark uncertain wording "FOUNDER TO CONFIRM" and ask.
- No figures of any kind from reports or the website: savings, profit, percentages, example numbers (R2).
- No em dash or en dash (R4). The lint hook will stop you; write it right the first time.
- Plain restaurant owner words, no finance jargon (R5). Two to four sentences, one question at a time (R6).
- Every new visitor-facing behaviour needs a row in docs/spec.md and at least one scripted test conversation.
- A guardrail in the prompt is never enough on its own: R1 to R4 and R8 must also be enforced in code (spec section 4).
