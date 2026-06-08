---
title: Maps of meaning and the economics of information search, discovery, and retrieval
summary: Reading is expensive.
tags: [hoplite, vision]
created: 2026-05-30
---

# Maps of meaning and the economics of information search, discovery, and retrieval

maximizing signal to noise

Search spends the frontier; discovery expands it.

An LLM-based agent works within a fixed context budget. It must act on a corpus larger than it can read. The agent has a limited set of built-in tools: glob, grep, and read. It can discover relationships with these tools, but it burns tokens, relies on error-prone judgement, and injects bias by reading off-task content. 

The default tools operate over surface text, recovering only content channels — lexical and topical overlap, a shared rare term. Relatedness carried by graph topology, by commit and authorship provenance, by temporal proximity is inexpensive to recover but unreachable: no graph exists to traverse, no history to read. These channels are recoverable after the corpus is reified as a graph.

Hoplite augments the default navigation tools through a map over the markdown corpus. Instead of relying on the agent to read, comprehend, and infer relationships on-the-fly, Hoplite applies structure to the markdown and reifies the map as a durable graph with declared and latent relationships. The agent navigates the map and reads selectively, spending its context on the subset that matters.

## The compounding cost of the grep-read-judge loop

Knowledge that sharpens the context is useful; the content carrying it is relevant. To acquire useful knowledge, the agent must locate and consume that content. The explore pipeline has three failure modes: extraction, reception, retention.

The agent's default method of exploration, `grep`, is a primitive search tool that returns unranked and unordered results. The agent must sift through hits, loading each into the context and judging usefulness for itself. The exploration loop taxes scarce resources: time, tokens, turns, context budget, and bias-inducing attention. The quantitative and qualitative costs compound. Every wasted read is debt serviced for the life of the context.

Scanned noise biases the agent; so does signal it never reaches. `grep` requires the agent's prior knowledge of a string pattern before it can search for it. Explore agents, guarding their context budget, scan excerpts and risk missing critical information — valuable terms for the follow-up search. Hard-won groundwork sits undiscovered. The knowledge-starved agent exercises poor judgment: it reopens settled decisions, contradicts conventions, ignores precedent, and reproduces prior art. Failures compound.

The agent pieces together its own map of meaning — the vocabulary in use, the documents that matter, the relationships among them. That map is the reward for every leaf it read and every dead end it ruled out. It lives in the context window and nowhere else. It dies with the session. The next agent rebuilds it from scratch. Or not. Cost compounds. Failure compounds. Knowledge that compounds is lost.

## Maximizing signal-to-noise

Hoplite builds a durable knowledge graph over the corpus — a map of meaning. Documents become nodes, relationships become edges, and the author's meta assertions build a surveyable vocabulary. The agent queries the map instead of scanning the bytes: it discovers the vocabulary, searches by relevance, walks relationships the filesystem can't express, and judges a document by its summary before reading. Locating and consuming — the costly acts — become a query and a choice.

The agent searches the map with rich predicates and shapes the result set projections. Walkable queries return ranked hits and gather the whole neighborhood in one turn. The agent judges the projection before spending tokens and context budget on the body. Noise sinks in the ranking, every read is earned, and the agent protects itself from bias by loading only content it trusts.

The agent surveys the vocabulary, encoded in the map, and queries the corpus in its own terms. It asks informed questions instead of guessing which string to `grep`. Search matches on meaning rather than a regular expression. The agent analyzes a signal-rich result set, not a sampled excerpt. Hits are ranked by IDF-weighted Jaccard over a unified feature set: content, metadata, and neighborhood. Relatedness surfaces in the ranking. Hard-won groundwork ranks among the results, no longer dark. The agent locates content it would have missed and trusts nothing is hidden.

The map is built once and persists. It outlives every session. The next agent inherits it instead of rebuilding from scratch: it walks to the rationale behind a decision before repeating it, and reads prior art before acting. The reward for every leaf read and every dead end ruled out is saved, not discarded. Every session adds to the graph; none starts from zero. Knowledge compounds.