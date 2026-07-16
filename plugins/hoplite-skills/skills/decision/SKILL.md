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

<what this costs, and what it buys>
```

Wikilink the terms and concepts the decision turns on, so it sits beside what it affects (link/edge syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).

Recoverable from the note alone: name the alternatives and the trade-off in full — the *why* must hold up without the conversation; never "the thing we discussed."

## Proofread

Reread the artifact before finishing. The register is engineering: the author is a software architect, the audience is software engineers and architects. Cut every tell of machine prose:

- Aphorisms. A closing line that sounds wise and says nothing → delete whole.
- Editorializing. "Importantly", "it's worth noting", "interestingly" — the reader decides what's notable; state the fact.
- Enthusiasm. "Powerful", "robust", "seamless", "comprehensive" → the measurable property, or nothing.
- Hedging. "Arguably", "perhaps", "somewhat" → commit to the claim or drop it.
- Announcing. Describing the content instead of saying it — "This note covers…", "Let's examine" → say the thing.
- One idea per sentence. A sentence you have to reread, clauses stacked past one thought → split it.
- Em dashes. More than one per paragraph → rewrite with periods.
- Empty contrast. "Not just X but Y", "X isn't about Y" → state the positive claim alone.
- Cohesion. Every paragraph advances the artifact's one claim; a stray that belongs elsewhere → move or cut.
- Consistency. Title, summary, and body make the same claim; a term means one thing throughout, and it's the glossary's meaning.

Fix what the sweep finds, then sweep the fix.
