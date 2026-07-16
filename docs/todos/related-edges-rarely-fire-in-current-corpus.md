---
title: Related edges rarely fire in current corpus
summary: Spot-checks against the spec and journal documents show zero `related` neighbors via `relatives`, despite MinHash running at build time. The connective tissue the `related` edge was meant to provide is largely absent — debugging needed before relying on similarity traversal.
tags: [note, hoplite, mcp, graph, related-edges, minhash, todo, bug]
created: 2026-05-26
priority: high
effort: medium
status: open
---

# Related edges rarely fire in current corpus

Spot-checks against the spec and journal documents show zero `related` neighbors via `relatives`, despite MinHash running at build time. The connective tissue the `related` edge was meant to provide is largely absent — debugging needed before relying on similarity traversal.

## Observation

In a 43-document, 82-edge corpus dumped at `2026-05-26T06-48-38.index.sqlite`, three traversals from semantically dense Hoplite documents returned no `related` neighbors at any depth:

- `journal/2026-05-25-1138-tag-model-evolution.md` — depth 2, direction both, edge_types=[`related`] → empty.
- `journal/2026-05-25-1137-eav-property-graph-refactor.md` — same predicate → empty.
- `hoplite/architecture.md`, `hoplite/tool-api.md` — same predicate, blocked by classifier mid-run, partial result was also empty.

If the `related` edge fired at the documented `DEFAULT_THRESHOLD = 0.20` Jaccard over MinHash signatures, the two journal entries from `2026-05-25` on the tag-model refactor share enough vocabulary and structure to clear that bar. They didn't.

## Suspected causes

1. Threshold too tight for the corpus. `plugins/hoplite/mcp/src/hoplite/minhash.py:70` sets `DEFAULT_THRESHOLD = 0.20`. Short journal entries with heavy boilerplate (frontmatter, headings, summary lines) may not clear it once MinHash sees the body.
2. Signature scope wrong. `graph.py:347` computes `minhash.signature(body)`, body only, summary excluded. Frontmatter summaries are some of the densest signal; their exclusion may starve the comparison.
3. Tokenization collapses too aggressively. If `minhash.signature` shingles by character n-grams or whitespace tokens without stopword handling, the markdown skeleton (headings, bullets, link syntax) may dominate the signature and wash out content overlap.
4. MinHash pass not actually emitting. The aggregate pass at `graph.py:363,450` may be silently dropping edges: a bytes-decoding round-trip, a signature comparison off-by-one, or a threshold inversion.

## Next

- Dump the index and inspect the `edges` table directly: count by `type`, look at distribution of `related` edges if any, sample their `confidence` values. Determines whether the pass is emitting nothing or emitting weakly.
- If emission is happening but sparse: sweep threshold downward (0.10, 0.05) and observe edge density.
- If emission is zero: read the aggregate pass at `graph.py:363,450` carefully against `minhash.jaccard` for a comparison bug.
- Consider whether summary text should fold into the signature alongside body.

## Why this matters

The `related` edge is the load-bearing differentiator for the graph against grep. It surfaces content adjacency without shared keywords or authored wikilinks. If it never fires, `relatives` collapses to wikilink traversal, which a human reader could follow by clicking. See [[docs/todos/mcp-reference-undersells-the-graph-against-grep.md]] for the related rhetoric problem.
