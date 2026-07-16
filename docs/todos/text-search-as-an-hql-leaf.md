---
title: Text search as an HQL leaf
summary: BM25 is orthogonal to predicate evaluation today — rewrite produces a candidate set, BM25 ranks within. A `text(query)` leaf in HQL folds text into the calculus but breaks set semantics — relations produce sets, BM25 produces rankings. Two paths if you want it in — top-k projection (lose rank) or carry scores through every operator (extend the calculus).
tags: [note, hoplite, mcp, design, architecture, hql, open-question, todo]
created: 2026-05-27
priority: low
effort: medium
status: open
blocked-by: ["[[hoplite-predicates-are-hql-rewrites-over-typed-relations]]"]
---

# Text search as an HQL leaf

BM25 is orthogonal to predicate evaluation today — rewrite produces a candidate set, BM25 ranks within. A `text(query)` leaf in HQL folds text into the calculus but breaks set semantics — relations produce sets, BM25 produces rankings. Two paths if you want it in — top-k projection (lose rank) or carry scores through every operator (extend the calculus).

## The orthogonality today

[[docs/todos/predicate-leaves-should-carry-relation-identity.md]] frames the layering: "BM25 stays orthogonal. The rewrite produces a candidate set; BM25 ranks textual relevance within it." Composition is two-stage — rewrite-narrow then BM25-rank, or BM25-overfetch then rewrite-filter — but the layers are distinct.

Under HQL ([[docs/todos/hoplite-predicates-are-hql-rewrites-over-typed-relations.md]]), relations produce usersets — sets of subject node IDs. The operator skeleton (`!`, `&`, `|`, `direct`, `computed`, `tuple`) is set algebra over those usersets. BM25 returns a ranked (subject, score) bag, not a userset, and the operator skeleton expects usersets.

## What a `text(...)` leaf expresses

The aspirational shape:

```
text("caching strategy") & tag(note)
```

"Notes about caching strategy." One expression instead of `where(text=..., tagged="note")` — text and predicate at the same syntactic level. The agent composes text with everything else HQL provides (edges, properties, traversal via `tuple`).

The same shape extends `relatives` symmetrically — `relatives(from_=..., predicate="text('caching') & tag(note)")` — text-rank within a walked neighborhood. `relatives` carries no text knob today; HQL with a `text(_)` leaf closes that gap.

## The set-semantics conflict

Relations produce sets. BM25 produces a (subject, score) bag. Two ways to reconcile:

1. Project to a set via top-k. `text("caching")` returns the top-N hits as a set, dropping the rank. The leaf is well-formed against the calculus. The cost: the composed query loses BM25 scoring. The reason for using text in the first place — surface the most relevant documents — collapses to "documents matching at all."
2. Extend the calculus to carry scores. Every operator becomes score-aware: `&` is min/product, `|` is max/sum, `!` is hard exclusion. The rewrite engine propagates scalar scores through every node. This is a real language change, closer to a fuzzy logic than a userset calculus. The Zanzibar heritage stops paying off here.

Both cost something. Top-k projection is the conservative choice; calculus extension is the ambitious one.

## The plumbing-only alternative

Add text to `relatives` as a parameter, not a leaf. The architecture supports this within HQL as it stands: predicate-narrow produces the walk's candidate set, and BM25 ranks it. This is the same two-stage shape as `where` today, applied to `relatives`. The calculus stays unchanged.

This delivers the user-facing capability (rank within a walk) at zero language-design cost. Text and predicates remain at separate syntactic levels — text as a tool parameter, predicates as the leaf calculus.

## See also

- [[docs/todos/hoplite-predicates-are-hql-rewrites-over-typed-relations.md]] — the HQL proposal this note extends and questions.
- [[docs/todos/predicate-leaves-should-carry-relation-identity.md]] — the orthogonality framing.
- [[docs/todos/rerank-bm25-candidates-with-graph-signals.md]] — the dual composition (BM25 first, graph reranks). Different stage order, same two-layer split.
