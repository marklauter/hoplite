---
name: glossary
description: Reduce a resolved term to its kernel — a word plus the smallest phrase that unpacks it — and write it to the Hoplite glossary. Use when a term settles, or when a definition needs collapsing, reducing, or locking.
---

# Glossary

A glossary entry is a term reduced to its kernel: the word, plus the smallest phrase that unpacks it in the domain. Reduce before you write; lock only when it's reduced and resolved.

- **Synonyms → collapse.** Several words for one idea → keep one canonical term, retire the rest into `document.retired`. If a retired word had its own glossary file, also list its old page name in `aliases` so existing links still resolve. "`couch`, `settee`, `davenport` name one thing → retire them to `sofa`."
- **Mechanism creeping in → strip it.** A definition carrying implementation → move that to the term it belongs to. "`engine` is *what converts fuel to motion* — not *the spark-plug firing order*; that's `ignition`'s job."
- **One word, two meanings → keep reducing.** An overloaded word is an incomplete reduction, not a kernel — each idea within the domain has its own precise word. Find the word for each sense and retire the overloaded one into them. You never write a second file under the same name. "`bug` did double duty → the creature sense reduced to `insect`, the fault sense to `defect`; `bug` retired into them, and — because `bug.md` existed — aliases `defect` too."
- **Reduced and resolved → lock.** The next cut would cost meaning, *and* the word carries one sense with its contrasts drawn → `document.status: locked`; until both hold, `evolving`.

Write `docs/hoplite/glossary/<term>.md` (kebab-case):

```markdown
---
title: <term>
summary: "<the smallest phrase that unpacks it>"
tags: [hoplite, glossary, <grouping>]
aliases: [<retired page name>, ...]
created: YYYY-MM-DD
document.status: <evolving | locked>
document.retired: [<retired term>, ...]
edge.specializes: [docs/hoplite/glossary:<broader-term>]
edge.contrast: [docs/hoplite/glossary:<other-term>, ...]
---

<the summary, verbatim>

## Examples

- <a concrete instance — the term in use, not more definition>

## Contrasts

- `<contrast-term>` — <one line drawing the boundary against it — never implementation detail>
```

- `aliases`, `document.retired`, `edge.specializes`, and `edge.contrast` are optional; omit when empty.
- **Edge targets follow the wikilink grammar** — every edge target (`edge.specializes`, `edge.contrast`) is namespace-qualified, no `.md`: `edge.contrast: [docs/hoplite/glossary:jaccard]`, not a file path. The full grammar lives in `docs/hoplite/defining-edges.md`.
- **Index it** — add `- [[docs/hoplite/glossary:<term>]]` to the `## Terms` list in `docs/hoplite/glossary/README.md`, kept alphabetical.
- **Reciprocate contrasts** — for every `edge.contrast` target, add this term back on that entry (contrast is mutual), and give it a bullet in the optional `## Contrasts` section drawing the boundary. One bullet per target; omit the section when there are none.
- **Specialize upward, never down** — a genus declares no edge to its species. The specialization edge points from the narrower term to the broader one (`edge.specializes`) and is *not* reciprocated: the genus stays ignorant of what extends it, so coining a new species never forces an edit to the parent. The asymmetric counterpart to reciprocated contrast — a contrast is mutual, a specialization is one-way.
- **Examples** — the optional `## Examples` section illustrates the term with concrete instances; the definition stays in the summary, and an example never restates it. Omit the section when there are none.
