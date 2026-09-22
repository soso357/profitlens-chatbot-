---
name: new-adr
description: Record an architecture or design decision in docs/adr/. Use right after Ioseb or a founder chooses between options, or when a decision is made that future sessions must not silently reverse.
---

# New ADR

1. Next number: highest in docs/adr/ plus one. Never reuse numbers.
2. Copy docs/adr/template.md to docs/adr/NNNN-short-title.md.
3. Context lists the options that were offered with their plain pros and cons. Decision names the chosen option and who chose it. Consequences include cost.
4. If it replaces an older ADR: new ADR says "Supersedes NNNN"; in the old one change only the Status line to "Superseded by NNNN".
5. Add one line to docs/build-log.md: `- YYYY-MM-DD: <decision> (ADR NNNN).`
6. If it changes a requirement, update docs/spec.md and cite the ADR next to the requirement.
Founder decisions (ADR 0001 to 0006) are only superseded with a founder's say-so.
