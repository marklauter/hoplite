# Term mechanism

How to write a resolved glossary term. The discipline (reduce to the kernel; lock when the next cut costs meaning) is in `SKILL.md`; this is the how.

## Write the entry

Path: `docs/hoplite/glossary/<term>.md`, where `<term>` is the term, kebab-case lowercase.

```markdown
---
title: <term>
summary: "<the smallest phrase that unpacks it in the domain>"
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

- `aliases` and `edge.contrast` are optional; omit the key when empty.
- `document.status`: `evolving` while contested, `locked` once it resolves.
- The body opens with the summary verbatim; the `**Also.**` line is optional and draws a boundary only.

Exemplar: `docs/hoplite/glossary/kind.md`.

## Index it

Add `- [[docs/hoplite/glossary/<term>.md]]` to the `## Terms` list in `docs/hoplite/glossary/README.md`, kept alphabetical.

## Reciprocate contrasts

For every path in this term's `edge.contrast`, add this term back to that file's `edge.contrast`. Contrast is mutual.

## Refresh

Call `refresh()` so later `where`/`relatives` queries see the write.
