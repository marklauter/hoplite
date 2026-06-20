---
name: spec
description: Compose a resolved concept from locked terms into the smallest spec document that still carries it, under docs/hoplite/. Use when a composite concept settles above the glossary.
---

# Spec

A spec document is a composite concept reduced to the smallest prose that still carries it, built from locked glossary terms. Stand it on the terms beneath it; lock when the next cut would cost meaning.

- **Build from terms.** Wikilink every glossary term the concept composes — `[[docs/hoplite/glossary/<term>.md]]` — at first use. "Affordances stand on `feature`, `edge`, `signifier` — link them, don't re-explain them."
- **Smallest that carries it.** Cut prose the concept doesn't need; a spec is a kernel, not a tour.
- **Next cut costs meaning → lock.** `locked` once it stops moving, `evolving` while it does.

Write `docs/hoplite/<concept>.md`:

```markdown
---
title: <concept>
summary: "<one line — what the concept is, built from its terms>"
tags: [hoplite, <domain>]
created: YYYY-MM-DD
document.status: <evolving | locked>
---

# <concept>

<the prose, composing the locked terms into the higher concept>
```

- Cross-reference adjacent specs where the connection is durable.
- Add the doc to the glossary README `## See also` when it anchors a cluster of terms.
