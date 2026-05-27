---
title: Hoplite predicates are PDL rewrites over typed relations
summary: Proposed predicate language for `where` and `relatives` — adopt Kingo's Zanzibar PDL rewrite calculus, generalize relations to cover frontmatter properties as value-parameterized relations, treat edges as relations too. Bare relation references at query time read as that relation's userset.
tags: [note, hoplite, mcp, design, architecture, todo]
created: 2026-05-27
aliases: []
---

# Hoplite predicates are PDL rewrites over typed relations

Proposed predicate language for `where` and `relatives` — adopt Kingo's Zanzibar PDL rewrite calculus, generalize relations to cover frontmatter properties as value-parameterized relations, treat edges as relations too. Bare relation references at query time read as that relation's userset.

## Background

PDL is the policy description language used in Kingo (`https://github.com/marklauter/kingo`), a Zanzibar-style ACL engine. It defines namespaces and relations; each relation has a *rewrite expression* that says how its userset is computed from explicit tuples, other relations, or edge walks. A userset and a node-id set are the same object — "subjects satisfying this rewrite" — which is why the calculus transfers cleanly to graph query.

The operator skeleton:

- Operators: `!` (exclusion), `&` (intersection), `|` (union). `!` binds tightest, then `&`, then `|`.
- Terms: `direct`, `computed <relation>`, `tuple(<edge-relation>, <target-relation>)`, or a parenthesized sub-rewrite.

The current Hoplite parser at `parser.py` already accepts `!`, `&`, `|`, parens, and bare kebab-case labels. The operator surface stays. The proposal extends what a leaf can be.

## Relations in Hoplite

[Inference] Hoplite has one node kind (document, day one) and three sources of relations:

- **Property relations** — each frontmatter key parameterized by value. `tag(notes)`, `tag(mcp)`, `status(draft)`, `priority(high)`, `aliases(foo)`. The userset of `tag(notes)` is the set of documents with a `node_properties` row where `(key='tags', value='notes')`. One indexed lookup per leaf.
- **Edge relations** — `mentions`, `related`. The userset of `mentions` on a focus document is the set of documents mentioned by it (or mentioning it; direction is a parameter).
- **Alias relations** — `aliases(foo)` resolves to the canonical document claiming `foo`. Loaded today, ungovernable through any tool — see [[notes/predicate-leaves-should-carry-relation-identity]].

[Guess] Value-parameterized relations deviate from strict PDL, where a relation is a bare identifier with no argument. Alternatives — one relation per (key, value) pair (`tag_notes`, `tag_mcp`, exploding by tag cardinality), or relations whose userset contains (subject, value) pairs rather than just subjects (changes the set algebra) — are worse in their own ways. Parameterization keeps the relation count bounded and the surface readable.

## Examples

```
tag(notes) & tag(mcp)
```
Documents tagged both `notes` and `mcp`.

```
tag(notes) & !status(draft)
```
Non-draft notes.

```
(tag(notes) | tag(journal)) & !tag(superseded)
```
Current notes or journal entries.

```
tuple(mentions, tag(architecture))
```
Documents that mention an architecture-tagged document.

```
tag(notes) & tag(open-question)
```
Notes that ask open questions.

Today's `notes & mcp` is the same query as `tag(notes) & tag(mcp)` with `tag(_)` implicit — a backward-compat shim, probably not worth keeping once explicit relations land.

## Operators and composition

[Inference] The three rewrite terms map onto Hoplite as:

- **`direct`** — explicit membership. For property relations, the EAV lookup. For edge relations, the materialized edge row.
- **`computed <r>`** — the userset of `r` on the current subject. Lets one relation reuse another's set on the same node. Bare `tag(notes)` at query position is shorthand for `computed tag(notes)`.
- **`tuple(<e>, <r>)`** — walk edge relation `e` from the current subject; for each reached subject, evaluate `r`; union the resulting subject sets. This is `traverse_nodes`' BFS expressed declaratively. Depth is a fix-point on `(self) | tuple(e, self)`; in practice the executor caps depth rather than computing convergence, and `relatives` retains its `depth` parameter.

## What this commits to

- PDL operators (`!`, `&`, `|`) and term keywords (`direct`, `computed`, `tuple`).
- Relations are typed; leaves carry relation identity through to the executor.
- Edges and properties unify as relations.
- Value parameterization on property relations.

## Open questions

- **Leaf surface syntax.** `tag(notes)` is one notation. Alternatives: `tag.notes`, `tag=notes`, `tag:notes`. Affects readability more than semantics; pick once and hold.
- **Range and comparison.** `created(2026-05-27)` is equality. Range queries (`created > 2026-01-01`, `priority >= 3`) need a leaf shape outside pure PDL — a comparison operator on parameterized relations.
- **Wildcards.** `tag(*)` meaning "any tag" — useful for "docs with tags" vs "docs without." Not in PDL; cheap to add, and the inverse `!tag(*)` reads naturally.
- **Subject scope split.** PDL is defined relative to an object. `relatives` has an explicit origin and walks from it; `where` has no origin and ranges over the whole corpus. `tuple(_, _)` semantics differ between the two — from the origin in `relatives`, from each candidate in `where`. Worth making explicit in the tool API.
- **Where the executor lives.** SQL against the live `node_properties` table, an in-memory inverted index per relation, or both. Touches the in-memory shape question — see [[notes/swap-in-memory-graph-dicts-for-property-graph-objects]].

## See also

- [[notes/predicate-leaves-should-carry-relation-identity]] — the design hole this proposal addresses. Today's predicate strips relation identity at the callsite; this note proposes the language that restores it.
- [[notes/swap-in-memory-graph-dicts-for-property-graph-objects]] — the in-memory shape axis. A relation-aware leaf executor needs an indexed lookup path; that note's inverted property index is one realization.
- [[notes/rerank-bm25-candidates-with-graph-signals]] — the rerank's tag-affinity feature consumes the same `(key, value)` lookup that property relations need. Shared executor.
