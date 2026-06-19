# Concept mechanism

How to write a resolved composite concept — a spec document built from locked terms. The discipline (reduce to the smallest spec that still carries the concept; same lock test) is in `SKILL.md`; this is the how.

## Write the document

Path: `docs/hoplite/hoplite-<concept>.md` — the existing spec naming (`hoplite-affordances.md`, `hoplite-frontmatter.md`, `hoplite-graph.md`).

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

## Build from locked terms

Wikilink every glossary term the concept composes — `[[docs/hoplite/glossary/<term>.md]]` — at first use. The links make the altitude explicit: the spec stands on the terms beneath it, and `relatives` walks down to them. Prefer linking a locked term to re-explaining it.

## Cross-reference siblings

Link adjacent spec documents where the connection is durable, and add the document to the glossary README `## See also` when it anchors a cluster of terms.

## Refresh

Call `refresh()` so later `where`/`relatives` queries see the write.
