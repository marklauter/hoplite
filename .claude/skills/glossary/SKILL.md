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
edges: [specializes::docs/hoplite/glossary:<broader-term>, contrast::docs/hoplite/glossary:<other-term>]
---

<the summary, verbatim>

## Examples

- <a concrete instance — the term in use, not more definition>

## Contrasts

- `<contrast-term>` — <one line drawing the boundary against it — never implementation detail>
```

- `aliases`, `document.retired`, and `edges` are optional; omit when empty.
- **Edges follow the wikilink grammar** — frontmatter edges are one `edges:` list; each entry is a `stereotype::target` string, the target namespace-qualified with no `.md`: `edges: [contrast::docs/hoplite/glossary:jaccard]`, not a file path and not an `edge.<stereotype>` key. The full grammar lives in `docs/hoplite/expressing-edges.md`.
- **Index it** — add `- [[docs/hoplite/glossary:<term>]]` to the `## Terms` list in `docs/hoplite/glossary/README.md`, kept alphabetical.
- **Examples** — the optional `## Examples` section illustrates the term with concrete instances; the definition stays in the summary, and an example never restates it. Omit the section when there are none.

## Edge stereotypes

A stereotype names the relationship an edge expresses, read as `<source> <stereotype> <target>`. The vocabulary is **open**: when a term relates to another in a way the known stereotypes don't capture, coin a verb that reads cleanly in that frame and just use it — no need to register it here. One rule places any stereotype, new or known: **direction follows dependency, and only symmetric edges reciprocate.**

- **Directional — the default.** When one term depends on another's meaning, the edge is written on the dependent's side only and points at the depended-upon. The target stays ignorant of what points at it, so coining a new dependent never forces an edit to the target. A freshly coined stereotype is directional unless the relationship genuinely reads identical from both ends. The known directional stereotypes:
  - `specializes::` — species → genus (a narrower term is-a broader one).
  - `uses::` — whole → part (a term built from a component).
  - `estimates::` — estimator → estimated (a term that approximates another's value).
- **Symmetric — reciprocated.** When the relationship reads the same from both ends, write it on both terms. The known symmetric stereotype is `contrast::` — a mutual boundary; for every `contrast::` edge, add this term back on the target and give it a `## Contrasts` bullet drawing the boundary. One bullet per target; omit the section when there are none.
