---
name: decision
description: Record a hard-to-reverse design decision as an ADR-equivalent note under docs/notes/. Use when a genuine trade-off is made — offer it before writing, never impose.
---

# Decision

A decision note records a choice hard enough to reverse that it earns a durable home. Record one only when all three hold — absent any, it's noise:

- **Hard to reverse.** Changing your mind later costs.
- **Surprising without context.** A future reader asks "why this way?"
- **A real trade-off.** Genuine alternatives, one chosen for reasons.

**Offer before you write.** A decision is consequential — name the choice and the alternatives, and write only on the user's agreement.

Write `docs/notes/<slug>.md` (kebab-case of the title):

```markdown
---
title: <the decision, stated as a claim>
summary: "<one line — what was decided and why>"
tags: [note, decision, <domain>]
created: YYYY-MM-DD
document.status: <evolving | locked>
---

# <the decision, stated as a claim>

<the decision>

## Alternatives

<the options considered, and why each was not chosen>

## Why

<the trade-off — what this choice costs, and what it buys>
```

Wikilink the terms and concepts the decision turns on, so it sits beside what it affects.
