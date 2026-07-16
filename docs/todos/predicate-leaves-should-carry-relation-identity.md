---
title: Predicate leaves should carry relation identity
summary: The tag predicate compiles a Zanzibar-style rewrite expression but strips relation identity at the callsite, leaving the engine able to ask only one question — "value X in tags?" — while node_properties already holds the full property graph.
tags: [note, todo, hoplite, mcp, design, architecture, open-question]
created: 2026-05-27
priority: low
effort: low
status: open
blocked-by: ["[[hoplite-predicates-are-hql-rewrites-over-typed-relations]]"]
---

# Predicate leaves should carry relation identity

The tag predicate compiles a Zanzibar-style rewrite expression but strips relation identity at the callsite, leaving the engine able to ask only one question — "value X in tags?" — while `node_properties` already holds the full property graph.

## The leak is at the callsite, not the grammar

The predicate parser produces `Callable[[frozenset[str]], bool]`, a flat set-membership check (parser.py:212, filtering.py:18). The expression layer (`!`, `&`, `|` with `direct`, `computed`, `tuple-to-subjectset`) is the rewrite calculus HQL formalizes, inherited from Zanzibar PDL via Kingo. It is superpowered, not the limit. The limit is `tools.py`: it materializes one relation's value set (a document's `tags` list) into a `frozenset[str]` and passes that in. By the time `filter_candidates` runs, the rewrite no longer knows the leaves were ever relations. The `tagged:` field on the predicate input is the choke point. It hard-binds the rewrite to `tags` and reduces the leaves to opaque strings.

## What carries relation identity restores

Each frontmatter key is a relation: `tags`, `aliases`, `status`, `priority`, `created`, user-defined. A `direct` leaf becomes `(relation, value)`, meaning "this node has `tags:hoplite` asserted." That's a `node_properties WHERE key=? AND value=?` lookup; the composite `(key, value)` index at graph.py:84 finally earns its keep. Edges (`mentions`, `related`) are relations too: same calculus, different storage. `computed <r>` composes relations on the same node. `tuple-to-subjectset(e, r)` walks edge `e` and evaluates relation `r` on the reached node, the rewrite-shaped form of `traverse_nodes`' BFS, generalized to any depth, direction, and composition.

## What collapses into one engine

This is contingent on the rewrite carrying relation identity through to evaluation:

- `where` tag filter → rewrite eval; the hard-bound relation goes away.
- `relatives` BFS → tuple-to-subjectset; depth becomes a fix-point on `(self) | tuple(edge, self)`.
- Aliases, created, summary, and user-defined keys → first-class predicates without new tool surface. "Which docs claim alias `foo`" is currently unanswerable through any tool despite being loaded into memory (graph.py:146). It falls out for free.

BM25 stays orthogonal. The rewrite produces a candidate set; BM25 ranks textual relevance within it. Composition order (rewrite-narrow then BM25-rank, or BM25-overfetch then rewrite-filter) is the same shape as today's tag post-filter, just honest about being a property-graph query.

## Shared lookup path with the graph-prior rerank

The same `node_properties WHERE key=? AND value=?` executor that lets predicates ask "is this doc tagged X" is what the graph-prior rerank needs for its tag-affinity feature (see [[docs/todos/rerank-bm25-candidates-with-graph-signals.md]]). That note proposes a two-stage retrieval: BM25 pulls the top 30–50 candidates by textual relevance, then a graph prior reranks them by topology relative to a focus document. The prior combines edge proximity, centrality, recency, and a tag-affinity bump when a candidate shares tags with the focus. Tag-affinity is structurally a `direct(tags, V)` leaf, the same EAV lookup, used as a scalar feature instead of a boolean filter.

The convergence generalizes. Any future signal computed from frontmatter properties (status-affinity, priority-weighted decay, `created`-date proximity, custom user-defined keys) bottoms out in the same `(node_id, key, value)` lookup. Build one relation-aware leaf executor, either an in-memory inverted property index or SQL against the live `node_properties` table once the runtime stops treating it as dump-only, and both consumers inherit the indexed path. The alternative duplicates the same access pattern in two places: predicate evaluation walking Python dicts, plus a separate ad-hoc feature pass for the rerank.

The dependency is one-directional: predicate-language work motivates the executor, and the rerank's per-candidate feature pass is what that executor also serves. Whichever lands first becomes the other's prototype. The strategic read is to design the executor as a shared service, a leaf-relation lookup returning a node-id set or a per-node scalar, rather than threading the same `node_properties` access through two unrelated call paths.

## What this doesn't say

This note frames the problem. The proposed language, HQL, is rewrites with typed, value-parameterized relations, and lives at [[docs/todos/hoplite-predicates-are-hql-rewrites-over-typed-relations.md]]. The `(relation, value)` and `direct(tags, V)` shorthand used above is illustrative, not committed surface; the proposal note works the syntactic decisions explicitly.

The in-memory shape hole (dicts vs object graph, inverted property index, multi-property AND without self-joins) lives at [[docs/todos/swap-in-memory-graph-dicts-for-a-property-graph-object-model.md]]. The two axes compose: a richer predicate language motivates the inverted index, and the index gives the predicate its sublinear path. The `documents_wide` mitigation in [[docs/specs/hoplite-roadmap.md#columnar-projection-for-multi-property-predicates]] is a scale-axis fix that doesn't bite until the predicate can express the queries in the first place. The upstream work is here.
