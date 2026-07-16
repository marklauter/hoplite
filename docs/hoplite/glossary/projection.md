---
title: projection
summary: "An ordered, capped, field-selected view of a result set — the form the agent reads."
tags: [hoplite, glossary]
created: 2026-06-19
status: evolving
---

An ordered, capped, field-selected view of a result set — the form the agent reads.

## Jobs

- **Order** — sort the hits by the relevance score a scoring condition attached, or by an intrinsic value like recency or centrality. [[match]] returns an unordered set and a scoring [[semantic-search]] condition only attaches a score; projection is the only operation that imposes an order.
- **Cap** — bound the number of hits and the depth of a [[walk]], so a query returns a budget, not the whole corpus.
- **Select fields** — return each hit's lede and tags rather than its body, so the agent judges relevance cheaply before spending tokens on the full document.
