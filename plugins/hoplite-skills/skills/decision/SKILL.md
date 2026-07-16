---
name: decision
description: Record a hard-to-reverse design decision as an ADR-equivalent note under docs/notes/.
disable-model-invocation: true
---

# Decision

A decision note records a choice hard enough to reverse that it earns a durable home. Record one only when all three hold — absent any, it's noise:

- Hard to reverse. Changing your mind later costs.
- Surprising without context. A future reader asks "why this way?"
- A real trade-off. Genuine alternatives, one chosen for reasons.

**Offer before you write.** A decision is consequential — name the choice and the alternatives, and write only on the user's agreement.

Write to the [Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide/welcome/) — plain and scannable; say what a thing is before how to use it.

Write `docs/notes/<slug>.md` (kebab-case of the title) to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`):

```markdown
---
title: <the decision, stated as a claim>
summary: "<one line — what was decided and why>"
tags: [note, decision, <domain>]
created: YYYY-MM-DD
status: <evolving | locked>
---

# <the decision, stated as a claim>

<the decision>

## Alternatives

<each option, and why it lost>

## Why

<the trade-off: what this costs, and what it buys>
```

Wikilink the terms and concepts the decision turns on, so it sits beside what it affects (link/edge syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).

Recoverable from the note alone: name the alternatives and the trade-off in full — the *why* must hold up without the conversation; never "the thing we discussed."

## Done when

- The user explicitly agreed to record it, and all three gate conditions hold.
- The alternatives and the trade-off are named in full — the why holds up without the conversation.
- The note lives at `docs/notes/<slug>.md`, meets the standard, passes the hook, and wikilinks the terms it turns on.
