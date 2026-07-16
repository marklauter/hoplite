---
title: Hoplite predicates are HQL rewrites over typed relations
summary: Proposed predicate language for `where` and `relatives` — HQL (Hoplite Query Language), a rewrite calculus inherited from Zanzibar PDL via Kingo. Generalizes relations to cover frontmatter properties as value-parameterized relations, treats edges as relations too. Bare relation references at query time read as that relation's userset.
tags: [note, hoplite, mcp, design, architecture, hql, todo]
created: 2026-05-27
priority: high
effort: high
status: open
---

# Hoplite predicates are HQL rewrites over typed relations

Proposed predicate language for `where` and `relatives` — HQL (Hoplite Query Language), a rewrite calculus inherited from Zanzibar PDL via Kingo. Generalizes relations to cover frontmatter properties as value-parameterized relations, treats edges as relations too. Bare relation references at query time read as that relation's userset.

## Background

HQL — Hoplite Query Language — is the proposed name. The calculus is inherited from Zanzibar, specifically the PDL (policy description language) used in Kingo, a Zanzibar-style ACL engine. The Kingo source is collected at [[docs/proxies/kingo-pdl.md]] — the README documents PDL syntax and semantics; the AclReader and AclWriter show a working evaluator binding the rewrite calculus to tuple storage. Useful precedent when HQL's executor design decisions want a concrete reference rather than a paper sketch.

PDL defines namespaces and relations; each relation has a *rewrite expression* that says how its userset is computed from explicit tuples, other relations, or edge walks. A userset and a node-id set are the same object — "subjects satisfying this rewrite" — which is why the calculus transfers cleanly to graph query.

The operator skeleton:

- Operators: `!` (exclusion), `&` (intersection), `|` (union). `!` binds tightest, then `&`, then `|`.
- Terms: `direct`, `computed <relation>`, `tuple(<edge-relation>, <target-relation>)`, or a parenthesized sub-rewrite.

The current Hoplite parser at `parser.py` already accepts `!`, `&`, `|`, parens, and bare kebab-case labels. The operator surface stays. The proposal extends what a leaf can be.

## Relations in Hoplite

Hoplite has one node kind (document, day one) and three sources of relations:

- Property relations — each frontmatter key parameterized by value. `tag(notes)`, `tag(mcp)`, `status(draft)`, `priority(high)`, `aliases(foo)`. The userset of `tag(notes)` is the set of documents with a `node_properties` row where `(key='tags', value='notes')`. One indexed lookup per leaf.
- Edge relations — `mentions`, `related`. The userset of `mentions` on a focus document is the set of documents mentioned by it (or mentioning it; direction is a parameter).
- Alias relations — `aliases(foo)` resolves to the canonical document claiming `foo`. Loaded today, ungovernable through any tool — see [[docs/todos/predicate-leaves-should-carry-relation-identity.md]].

Value-parameterized relations deviate from strict PDL (HQL's heritage), where a relation is a bare identifier with no argument. The alternatives are worse in their own ways: one relation per (key, value) pair (`tag_notes`, `tag_mcp`) explodes by tag cardinality, and relations whose userset contains (subject, value) pairs rather than just subjects change the set algebra. Parameterization keeps the relation count bounded and the surface readable.

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

The three rewrite terms map onto Hoplite as:

- `direct` — explicit membership. For property relations, the EAV lookup. For edge relations, the materialized edge row.
- `computed <r>` — the userset of `r` on the current subject. Lets one relation reuse another's set on the same node. Bare `tag(notes)` at query position is shorthand for `computed tag(notes)`.
- `tuple(<e>, <r>)` — walk edge relation `e` from the current subject; for each reached subject, evaluate `r`; union the resulting subject sets. This is `traverse_nodes`' BFS expressed declaratively. Depth is a fix-point on `(self) | tuple(e, self)`; in practice the executor caps depth rather than computing convergence, and `relatives` retains its `depth` parameter.

## What this commits to

- HQL operators (`!`, `&`, `|`) and term keywords (`direct`, `computed`, `tuple`).
- Relations are typed; leaves carry relation identity through to the executor.
- Edges and properties unify as relations.
- Value parameterization on property relations.

## Open questions

- Leaf surface syntax. `tag(notes)` is one notation. Alternatives: `tag.notes`, `tag=notes`, `tag:notes`. Affects readability more than semantics; pick once and hold.
- Range and comparison. `created(2026-05-27)` is equality. Range queries (`created > 2026-01-01`, `priority >= 3`) need a leaf shape outside pure HQL — a comparison operator on parameterized relations.
- Wildcards. `tag(*)` meaning "any tag" — useful for "docs with tags" vs "docs without." Not in HQL today; cheap to add, and the inverse `!tag(*)` reads naturally.
- Subject scope split. HQL is defined relative to an object. `relatives` has an explicit origin and walks from it; `where` has no origin and ranges over the whole corpus. `tuple(_, _)` semantics differ between the two — from the origin in `relatives`, from each candidate in `where`. Worth making explicit in the tool API.
- Where the executor lives. SQL against the live `node_properties` table, an in-memory inverted index per relation, or both. Touches the in-memory shape question — see [[docs/todos/swap-in-memory-graph-dicts-for-a-property-graph-object-model.md]].

## See also

- [[docs/todos/predicate-leaves-should-carry-relation-identity.md]] — the design hole this proposal addresses. Today's predicate strips relation identity at the callsite; this note proposes the language that restores it.
- [[docs/todos/swap-in-memory-graph-dicts-for-a-property-graph-object-model.md]] — the in-memory shape axis. A relation-aware leaf executor needs an indexed lookup path; that note's inverted property index is one realization.
- [[docs/todos/rerank-bm25-candidates-with-graph-signals.md]] — the rerank's tag-affinity feature consumes the same `(key, value)` lookup that property relations need. Shared executor.
