---
name: glossary
description: Reduce a resolved term to its kernel — a word plus the smallest phrase that unpacks it — and write it to the hoplite glossary. Use when a term settles, or when a definition needs collapsing, splitting, or locking.
---

# Glossary

A glossary entry is a term reduced to its kernel: the word, plus the smallest phrase that unpacks it in the domain. Reduce before you write; lock only when the next cut would cost meaning.

- **Synonyms → collapse.** Several words for one idea → keep one, list the rest as `aliases`. "`declare`, `authored`, `declared` name one act → alias them to `assert`."
- **Mechanism creeping in → strip it.** A definition carrying implementation → move that to the term it belongs to. "`assert` is *to make a claim* — not *a wikilink in body text*; that's `wikilink`'s job."
- **One word, two meanings → split.** An overloaded term → two entries. "`declared` the authoring verb vs `declared` the edge kind → two entries."
- **Next cut costs meaning → lock.** Reduced as far as it goes → `document.status: locked`; until then, `evolving`.

Write `docs/hoplite/glossary/<term>.md` (kebab-case):

```markdown
---
title: <term>
summary: "<the smallest phrase that unpacks it>"
tags: [hoplite, glossary]
created: YYYY-MM-DD
document.status: <evolving | locked>
document.category: <domain grouping, e.g. edge anatomy>
aliases: [<retired synonym>, ...]
edge.contrast: [docs/hoplite/glossary/<other-term>.md, ...]
---

<the summary, verbatim>

**Also.** <one line drawing the boundary against a contrast term — never implementation detail>
```

- `aliases` and `edge.contrast` are optional; omit when empty. Exemplar: `kind.md`.
- **Index it** — add `- [[docs/hoplite/glossary/<term>.md]]` to the `## Terms` list in `docs/hoplite/glossary/README.md`, kept alphabetical.
- **Reciprocate contrasts** — for every `edge.contrast` target, add this term back on that entry. Contrast is mutual.
