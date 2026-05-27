---
title: Swap in-memory graph dicts for a property-graph object model
summary: Hand-rolled adjacency dicts today; explore swapping to an object Graph<Node, Edge> once query patterns push past simple BFS and single-property filters.
tags: [note, todo, hoplite, refactor, in-memory, graph]
created: 2026-05-25
aliases: []
priority: low
effort: high
---

# Swap in-memory graph dicts for a property-graph object model

Hand-rolled adjacency dicts today; explore swapping to an object `Graph<Node, Edge>` once query patterns push past simple BFS and single-property filters.

## Motivation

The day-one in-memory model is dicts of dataclasses — `documents: dict[str, Document]`, `out_edges: dict[str, list[Edge]]`, `node_properties: dict[str, dict[str, list[str]]]`, and so on. Every Hoplite query (BFS in `traverse_nodes`, predicate filter in `match_nodes`, ghost materialization in the walker) goes through plain dict lookups. The graph structure is implied by the access pattern; the type system doesn't enforce it.

Persistence isn't a constraint — the SQLite dump is a one-shot debug serialization, not the source of truth. The in-memory representation can be whatever fits the workload. That means a proper object graph is on the table whenever it pays for itself.

## What a Graph<Node, Edge> object model would give us

- **Cleaner API.** `node.neighbors(kind="mentions")` and `node.props["tags"]` read better than `graph.out_edges.get(path, [])` plus `graph.node_properties.get(path, {}).get("tags", [])`.
- **Invariant safety.** `out_edges` and `in_edges` are two views of the same graph that can drift apart under careless mutation. A `Graph.add_edge(src, dst, kind)` that maintains both atomically removes the failure mode.
- **In-memory secondary indexes.** "All docs with `status='draft'`" today either scans `node_properties` or falls back to the SQLite dump. An object graph that maintains an inverted property index on every insert serves the lookup in O(1) without leaving Python.
- **Path-traversal idioms.** Cypher-shaped patterns ("from X, follow mentions, then related, depth ≤ 2") fall out naturally when nodes and edges are objects that know how to walk.
- **Edge properties as first-class.** `edge.confidence` reads better than `graph.edge_properties[(src, dst, kind)]["confidence"][0]`.

## What we'd give up

- **Dependency choice.** NetworkX is the obvious off-the-shelf option but heavyweight and Python-pure — often slower than direct dicts at corpus scale.
- **Object overhead.** At thousands of docs the cost is invisible. At hundreds of thousands the dict-of-list version may still win.
- **Migration cost.** Tools.py and graph.py both touch the in-memory model; a swap means coordinated edits.

## Reference

The author's own graph-design repo collects in-memory shape experiments worth lifting ideas from: https://github.com/marklauter/graph

Branches there explore adjacency list, adjacency matrix, incidence list, object-graph-with-bidirectional-links, and other shapes. Hoplite's read pattern is "small fan-out, single-hop traversal, occasional BFS to depth ≤ 3, single-property predicate filter" — pick the shape whose access cost matches.

## Trigger

Worth doing when query patterns push past what dicts gracefully serve. Concretely, when any of these arrive:

- Multi-property predicates that today require self-joins on the dump (see [[docs/hoplite/hoplite-roadmap.md#columnar-projection-for-multi-property-predicates|columnar projection in roadmap]]) — an in-memory inverted index would serve them without leaving Python.
- Embedding-similarity scoring blended with graph traversal in a single query.
- Path-finding queries beyond simple BFS — shortest path, transitive closure, hub detection.
- The Edge dataclass starts wanting more behavior than just data.

Until then, dicts work. The structure stays a hand-rolled property graph, just described in primitives.

## Next

- Skim the branches at https://github.com/marklauter/graph, pick a shape that fits Hoplite's read patterns.
- Prototype a Graph<Node, Edge> swap of just the in-memory model — keep the walker, tools, and dump schema unchanged.
- Measure: does the API get cleaner without breaking anything? Does any query simplify?
- If the prototype reads well, lean in. If it doesn't, dicts win — close the question as resolved.
