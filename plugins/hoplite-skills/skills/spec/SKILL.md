---
name: spec
description: Compose a resolved concept from locked terms into the smallest spec document that still carries it, under docs/hoplite/. Use when a composite concept settles above the glossary.
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
