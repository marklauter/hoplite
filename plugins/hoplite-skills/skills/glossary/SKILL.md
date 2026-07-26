---
name: glossary
description: Reduce a concept to the single term that names it, then reduce that term's definition to its kernel, a statement of genus and differentiae. Use when a term settles, or when a definition needs collapsing, reducing, or locking.
---

A glossary is a set of terms that carries the ubiquitous language of a domain model. Each entry fixes one concept in the domain and gives it the single term that carries it precisely. Modeling simplifies the real world, so the many words offered by ordinary speech for a concept are reduced to one that best serves the model.

A definition is a statement that fixes a term's meaning by naming the nearest class to which the term belongs and the property that distinguishes it within that class. It is a single statement that contains the genus and its differentiae and nothing else. Keep cutting until the next cut would take the genus or a differentia. What's left after the cuts is the kernel.

Search `docs/glossary/` before writing. A concept already named keeps its entry, and a term that names a concept the glossary already carries breaks the one concept, one term rule before it is written.

Writing an entry takes two reductions. The first narrows a concept to the single term that names it. The second narrows that term's meaning to the kernel the entry carries. Reduce before you write.

Obey these logical rules when reducing terms to their kernel:

1. State genus and differentiae — the essence, not accidents.
2. Be coextensive — neither too broad nor too narrow.
3. Don't be circular — the definiens can't contain the definiendum, directly or through a chain.
4. Don't be obscure or figurative — the definiens must be better known than the definiendum.
5. Be affirmative — a negation names a complement, and a complement isn't a class.

A noun kernel opens with an indefinite article and its genus. A verb kernel opens with the infinitive.

The glossary maps each concept to exactly one term, and every statement sits on the term it describes. Repair the map when either breaks.

- Collapse several words for one concept into the canonical one, and split one word carrying several concepts into a word per sense. Delete the entries you retire and repoint their wikilinks. "`couch`, `settee`, and `davenport` collapse to `sofa`. `bug` splits into `insect` and `defect`."
- Define the domain, not the build. A kernel stays true after a rewrite in another language, so a type, function, module, or layer name never appears in one.
- Move mechanism to the term it describes. "`engine` is *a machine that converts fuel to motion*, not *the spark-plug firing order*, which belongs to `ignition`."

The glossary is coherent when every term is satisfiable. A term whose genus, differentiae, and disjointness claims cannot all hold at once names nothing.

Walk the edges before locking a term. Follow `is-a` to the root and confirm the term never appears on its own path. Follow `has-a` and confirm the term never contains itself along the chain. Read the genus chain you land on and confirm each differentia narrows what the chain already says. Check every `disjoint-with` and confirm it points at a sibling under a shared genus rather than a class the term descends from. A term that fails any of these has the wrong genus or the wrong `disjoint-with`, so fix one and walk again.

Lock the term when the walk passes, the next cut would cost meaning, and the word carries one sense with its disjoint terms named. Set `status: locked`. Otherwise set `status: evolving`.

## Structure

Write `docs/glossary/<term>.md` (kebab-case) to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`):

```markdown
---
title: <term>
type: definition
summary: "<the kernel>"
tags: [glossary, <optional-grouping>]
created: YYYY-MM-DD
status: <evolving | locked>
is-a: "[[<broader-term>]]"
disjoint-with:
  - "[[<other-term>]]"
  - "[[<another-term>]]"
---

<the kernel, verbatim>

## Examples

- <a concrete instance — the term in use, not more definition>

## Rationale

<what the kernel cannot carry — why this genus, what the boundary excludes, what was rejected>
```

- An edge is a property whose value is a quoted wikilink — the key names the relationship, the value the target, like `is-a: "[[...]]"`; there is no `edges:` list and no `edge.` prefix (edge/link syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).
- Examples — the optional `## Examples` section illustrates the term with concrete instances; the definition stays in the summary, and an example never restates it. Omit the section when there are none.
- Rationale — the optional `## Rationale` section holds what the kernel cannot carry, such as why this genus was chosen, what the boundary excludes, or which candidate terms lost. It never redefines the term, and dated history belongs in the journal. Omit the section when there is nothing to say.

## Edge keys

The frontmatter key names the relationship the edge expresses, read `<source> <key> <target>`. The vocabulary is open, but reach for a recognized relation below before coining a new one. Edge direction follows dependency; only symmetric edges reciprocate.

- Directional — the default. The edge lives on the dependent's side and points at what it depends on; the target stays ignorant, so a new dependent never edits it.
  - `is-a:` — species → genus. Transitive.
  - `has-a:` — whole → part. Not transitive, and a part never inherits the whole's genus.
- Symmetric — reciprocated. The relationship reads identical from both ends, so write it on both terms. Add `disjoint-with` back on the target pointing here.
  - `disjoint-with:` — a sibling under the same genus; no instance is both.

## Proofread

The artifact is not done until it has been proofread. Before presenting it, committing it, or ending the turn, invoke the `proofreading` skill (`hoplite-skills:proofreading` via the Skill tool) and follow its instructions on the artifact.