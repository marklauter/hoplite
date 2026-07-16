---
name: spec
description: Compose a resolved concept from locked terms into the smallest spec under docs/hoplite/.
disable-model-invocation: true
---

# Spec

A spec document is a composite concept reduced to the smallest prose that still carries it, built from locked glossary terms. Stand it on the terms beneath it; lock when the next cut would cost meaning.

- Build from terms. Wikilink every glossary term the concept composes — `[[<term>]]` — at first use (link/edge syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`). "Affordances stand on `feature`, `edge`, `signifier` — link them, don't re-explain them."
- Smallest that carries it. Cut prose the concept doesn't need.
- Next cut costs meaning → lock. `locked` once it stops moving, `evolving` while it does.

Write to the [Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide/welcome/) — plain and scannable; say what a thing is before how to use it.

Write `docs/hoplite/<concept>.md` to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`):

```markdown
---
title: <concept>
summary: "<one line — what the concept is, built from its terms>"
tags: [hoplite, <domain>]
created: YYYY-MM-DD
status: <evolving | locked>
cites:
  - "[[<term>]]"
  - "[[<other-term>]]"
---

# <concept>

<the prose, composing the locked terms into the higher concept>
```

- Cross-reference adjacent specs where the connection is durable.
- Add the doc to the glossary README `## See also` when it anchors a cluster of terms.
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
