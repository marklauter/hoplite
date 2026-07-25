---
name: glossary
description: Reduce a concept to the single term that names it, then reduce that term's definition to its kernel, a statement of genus and differentiae. Use when a term settles, or when a definition needs collapsing, reducing, or locking.
---

A glossary is a set of terms that carries the ubiquitous language of a domain model. Each entry fixes one concept in the domain and gives it the single term that carries it precisely. Modeling simplifies the real world, so the many words offered by ordinary speech for a concept are reduced to one that best serves the model.

A definition is a statement that fixes a term's meaning by naming the nearest class to which the term belongs and the property that distinguishes it within that class. It is a single statement that contains the genus and its differentiae and nothing else. Keep cutting until the next cut would take the genus or a differentia. What's left after the cuts is the kernel.

Writing an entry takes two reductions. The first narrows a concept to the single term that names it. The second narrows that term's meaning to the kernel the entry carries. Reduce before you write, and lock only when the kernel is reduced and resolved.

Obey these logical rules when reducing terms to their kernel:

1. State genus and differentiae — the essence, not accidents.
2. Be coextensive — neither too broad nor too narrow.
3. Don't be circular — the definiens can't contain the definiendum, directly or through a chain.
4. Don't be obscure or figurative — the definiens must be better known than the definiendum.
5. Be affirmative — a negation names a complement, and a complement isn't a class.

A noun kernel opens with an indefinite article and its genus. A verb kernel opens with the infinitive.

- Several words for one idea are one term. Keep the canonical word, delete the others, and repoint their wikilinks. "`couch`, `settee`, and `davenport` name one thing, so only `sofa` gets an entry."
- Mechanism belongs to the term it describes, so move it there. "`engine` is *a machine that converts fuel to motion*, not *the spark-plug firing order*, which belongs to `ignition`."
- An overloaded word is an incomplete reduction. Give each sense its own word, delete the overloaded entry, and repoint its wikilinks at the sense meant. "`bug` split into `insect` and `defect`."
- A term locks when it is reduced and resolved. The next cut would cost meaning, and the word carries one sense with its contrasts drawn; that entry takes `status: locked`. Until both hold it stays `evolving`.

The glossary is coherent when every term is satisfiable. A term whose genus, differentiae, and contrasts cannot all hold at once names nothing.

Walk the edges before locking a term. Follow `is-a` to the root and confirm the term never appears on its own path. Read the genus chain you land on and confirm each differentia narrows what the chain already says. Check every contrast and confirm it points at a sibling under a shared genus rather than a class the term descends from. A term that fails any of these has the wrong genus or the wrong contrast, so fix one and walk again.

Write to the [Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide/welcome/) — plain and scannable; say what a thing is before how to use it.

## Structure

Write `docs/glossary/<term>.md` (kebab-case) to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`):

```markdown
---
title: <term>
type: definition
summary: "<the kernel>"
tags: [glossary, <grouping>]
created: YYYY-MM-DD
status: <evolving | locked>
is-a: "[[<broader-term>]]"
contrast:
  - "[[<other-term>]]"
  - "[[<another-term>]]"
---

<the kernel, verbatim>

## Examples

- <a concrete instance — the term in use, not more definition>

## Contrasts

- `<contrast-term>` — <one line drawing the boundary against it — never implementation detail>
```

- An edge is a property whose value is a quoted wikilink — the key names the relationship, the value the target, like `is-a: "[[...]]"`; there is no `edges:` list and no `edge.` prefix (edge/link syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).
- Index it — add `- [[<term>]]` to the `## Terms` list in `docs/glossary/README.md`, kept alphabetical.
- Examples — the optional `## Examples` section illustrates the term with concrete instances; the definition stays in the summary, and an example never restates it. Omit the section when there are none.

## Edge keys

The frontmatter key names the relationship the edge expresses, read `<source> <key> <target>`. The vocabulary is open, but reach for a recognized relation below before coining a new one. Edge direction follows dependency; only symmetric edges reciprocate.

- Directional — the default. The edge lives on the dependent's side and points at what it depends on; the target stays ignorant, so a new dependent never edits it.
  - `is-a:` — species → genus. Transitive.
  - `has-a:` — whole → part.
- Symmetric — reciprocated. The relationship reads identical from both ends, so write it on both terms: add this term back on the target and give it a `## Contrasts` bullet, one per target.
  - `contrast:` — opposite; a mutual boundary.

## Proofread

The artifact is not done until it has been proofread. Before presenting it, committing it, or ending the turn, invoke the `proofreading` skill (`hoplite-skills:proofreading` via the Skill tool) and follow its instructions on the artifact.
