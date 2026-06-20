---
name: glossary
description: Reduce a resolved term to its kernel — a word plus the smallest phrase that unpacks it — and write it to the Hoplite glossary. Use when a term settles, or when a definition needs collapsing, splitting, or locking.
---

# Glossary

A glossary entry is a term reduced to its kernel: the word, plus the smallest phrase that unpacks it in the domain. Reduce before you write; lock only when the next cut would cost meaning.

- **Synonyms → collapse.** Several words for one idea → keep one canonical term, retire the rest into `document.retired`. If a retired word had its own glossary file, also list its old filename in `aliases` so existing links still resolve. "`declare`, `author`, `describe` name one act → retire them to `assert`."
- **Mechanism creeping in → strip it.** A definition carrying implementation → move that to the term it belongs to. "`assert` is *to make a claim* — not *a wikilink in body text*; that's `wikilink`'s job."
- **One word, two meanings → not fully reduced.** An overloaded word is an incomplete reduction, not a kernel — each idea within the domain has its own precise word. Find the word for each sense and retire the overloaded one into them. You never write a second file under the same name. "`declared` did double duty → the act reduced to `assert`, the edge sense to its own provenance term; `declared` retired into them, and — because `declared.md` existed — aliases `assert` too."
- **Next cut costs meaning → lock.** Reduced as far as it goes → `document.status: locked`; until then, `evolving`.

Write `docs/hoplite/glossary/<term>.md` (kebab-case):

```markdown
---
title: <term>
summary: "<the smallest phrase that unpacks it>"
tags: [hoplite, glossary]
aliases: [<retired filename>, ...]
created: YYYY-MM-DD
document.status: <evolving | locked>
document.retired: [<retired term>, ...]
document.category: <domain grouping, e.g. edge anatomy>
edge.contrast: [docs/hoplite/glossary/<other-term>.md, ...]
---

<the summary, verbatim>

## Contrasts

- `<contrast-term>` — <one line drawing the boundary against it — never implementation detail>
```

- `aliases`, `document.retired`, and `edge.contrast` are optional; omit when empty.
- **Index it** — add `- [[docs/hoplite/glossary/<term>.md]]` to the `## Terms` list in `docs/hoplite/glossary/README.md`, kept alphabetical.
- **Reciprocate contrasts** — for every `edge.contrast` target, add this term back on that entry (contrast is mutual), and give it a bullet in the optional `## Contrasts` section drawing the boundary. One bullet per target; omit the section when there are none.
