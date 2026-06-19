# Decision mechanism

How to write a resolved decision — an ADR-equivalent note. The discipline (the three-condition gate; offer, don't impose) is in `SKILL.md`; this is the how.

## Offer first

A decision is hard to reverse, so propose it before writing — name the choice and the alternatives, and let the user confirm. Write only on agreement.

## Write the note

Path: `docs/notes/<slug>.md`, where `<slug>` is the kebab-case H1 title.

```markdown
---
title: <the decision, stated as a claim>
summary: "<one line — what was decided and why>"
tags: [note, decision, <domain>]
created: YYYY-MM-DD
document.status: <evolving | locked>
---

# <the decision, stated as a claim>

<the decision>

## Alternatives

<the options considered, and why each was not chosen>

## Why

<the trade-off — what this choice costs, and what it buys>
```

Wikilink the terms and concepts the decision turns on, so it sits in the graph beside what it affects.

## Refresh

Call `refresh()` so later `where`/`relatives` queries see the write.
