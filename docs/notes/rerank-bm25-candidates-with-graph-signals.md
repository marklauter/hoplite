---
title: Rerank BM25 candidates with graph signals
summary: Hoplite's categorical differentiator over off-the-shelf retrievers — let BM25 pull top-N candidates, then rerank by edge proximity, centrality, and recency. The graph is data no general retriever has for this corpus. Pairs naturally with a cross-encoder reranker for the lexical-semantic gap.
tags: [note, hoplite, mcp, retrieval, design, todo]
created: 2026-05-27
aliases: []
document.priority: medium
document.effort: high
document.status: open
edge.blocked_by: [docs/notes/related-edges-rarely-fire-in-current-corpus.md]
---

# Rerank BM25 candidates with graph signals

Hoplite's categorical differentiator over off-the-shelf retrievers — let BM25 pull top-N candidates, then rerank by edge proximity, centrality, and recency. The graph is data no general retriever has for this corpus. Pairs naturally with a cross-encoder reranker for the lexical-semantic gap.

## Mechanism

Two-stage retrieval. First stage: BM25 (or hybrid BM25 + dense) returns the top 30–50 candidates by textual relevance. Second stage: rerank that set by a graph prior, then return top-k.

The graph prior is a scalar per candidate computed from features the graph already exposes — wikilink (`mentions`) edges, MinHash (`related`) edges with confidence, document recency, in-degree. Combine via a weighted sum, or a small learned model, or RRF against the textual ranker.

## Why this is Hoplite-shaped

[Inference] Every general retriever — BM25, dense embeddings, hybrid, cross-encoder rerank — operates on text alone. Each treats documents as bags of tokens or vectors of meaning. None has access to *how the corpus is wired*. Hoplite does. The wikilinks the author placed and the MinHash adjacencies the indexer inferred are signal no off-the-shelf RAG library can use, because they don't exist outside this index.

Closing the lexical-semantic gap with a cross-encoder is a commodity upgrade; many retrievers do it. Reranking by graph topology is the move that can't be replicated by swapping in a better off-the-shelf component.

## Candidate signals

- **Edge proximity to a focus node.** When the agent is working on or just read document D, boost candidates with short graph distance to D. One hop via `mentions` or `related` outranks two hops. Weight by edge confidence for `related`.
- **Centrality / PageRank.** Highly-connected documents are likely hubs — design docs, architecture overviews, frequently-cited references. A small centrality boost surfaces them when textual scores tie.
- **Recency.** Notes and journal entries decay in relevance; a recency prior on `created` (or `mtime` from the filesystem) lifts recent material when the query has no temporal anchor.
- **Tag affinity to the focus node.** If the focus document is tagged `mcp`, candidates sharing that tag get a small boost. Cheap; uses existing index data.

## Dependencies and risks

- [Observation] The `related` edge currently rarely fires — see [[docs/notes/related-edges-rarely-fire-in-current-corpus.md]]. Until that's fixed, the graph prior collapses to wikilinks + tags + recency, losing the inferred-adjacency signal that distinguishes graph-aware retrieval from "follow the links the author wrote." Reranking quality depends on `related` edges working.
- [Guess] On a corpus this small (tens of documents), the graph prior may overfit — a few wikilinks dominate the topology, and the rerank becomes deterministic. The signal sharpens as the corpus grows; worth measuring before claiming a quality win.
- [Inference] A "focus node" requires the agent to declare one — implicit (last document read in the session) or explicit (passed as a query parameter). The implicit version needs state the MCP server doesn't currently carry; the explicit version needs the agent to know what to pass.

## Where it sits relative to other upgrades

A cross-encoder rerank on BM25 candidates is the highest-leverage *textual* upgrade — closes the keyword-vs-meaning gap for one model load and ~100ms latency. A graph-prior rerank is the highest-leverage *structural* upgrade — uses data only this index has.

Stack them. BM25 retrieves top-50, cross-encoder rescores by joint query-document attention, graph prior boosts by topology relative to a focus node. The first stage is recall; the second stage is textual precision; the third stage is contextual fit to where the agent is in the corpus.

## See also

- [[docs/notes/related-edges-rarely-fire-in-current-corpus.md]] — load-bearing dependency. The graph prior loses its inferred-adjacency signal until MinHash edges actually fire.
- [[docs/notes/mcp-reference-undersells-the-graph-against-grep.md]] — adjacent intervention. That note is about *prose framing* to redirect agents to existing tools; this note is about an *algorithmic* upgrade to the matching itself. Both make Hoplite categorically different from grep, at different layers.
