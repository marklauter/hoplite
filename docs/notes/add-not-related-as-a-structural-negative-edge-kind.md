---
title: Not-related stereotype subtracts from inferred related
summary: not-related is the first structural-negative stereotype on the mentions edge — it labels a wikilink (or frontmatter edge entry) where the author declines an inferred similarity. The existing mention-skip logic gives it suppression behavior for free.
tags: [note, hoplite, edges, stereotypes, not-related, design, todo]
created: 2026-05-27
priority: low
effort: medium
status: open
---

# Not-related stereotype subtracts from inferred related

`not-related` is the first structural-negative stereotype on the `mentions` edge — it labels a wikilink (or frontmatter edge entry) where the author declines an inferred similarity. The existing mention-skip logic gives it suppression behavior for free.

## Why the stereotype earns its place

[Observation] MinHash false positives are routine. Two documents can share a vocabulary spike without sharing a topic — one note discusses MinHash for similarity ranking, another critiques MinHash as a primitive for a different reason, and the shared tokens light up the inferred edge. The pair scores high; the relationship is spurious.

[Inference] The corpus author is the only entity who knows the spurious cases. Lowering the MinHash threshold trades recall for precision globally; tagging individual false positives is a per-pair correction that stays surgical. The author has signal the algorithm cannot derive.

## Three-category model

[Inference] Adding `not-related` splits the stereotype taxonomy into three categories:

- Structural positive, rhetorical positive — `mentions` with no stereotype, `cites`, and stereotypes like `supports`. Authored alignment.
- Structural positive, rhetorical negative — `contradicts`, tracked in [[docs/notes/add-contradicts-as-an-authored-edge-kind.md]]. Authored disagreement that still asserts a relationship.
- Structural negative — `not-related`. Author declines an inferred relationship.

[Inference] The first two categories assert a relationship exists. `not-related` is the first stereotype that asserts a relationship does not exist — a structural denial rather than a rhetorical position.

## Semantics: set subtraction via mention-skip

[Inference] `_emit_related_edges` already maintains a skip-set of authored pairs at `plugins/hoplite/mcp/src/hoplite/graph.py`. Under the stereotype model, that skip-set covers `not-related` without code change:

`skip = { (src, dst) | mentions edge exists between them, regardless of stereotype }`

Any pair in the skip-set bypasses the inferred-edge emission. A `not-related` mention is still a mention — it lands in the skip-set the same way a neutral mention or a `contradicts` mention does. The suppression mechanism is the existing mention-skip behavior, viewed from a different angle.

[Inference] Direction is symmetric. Authoring `[[B]]<!--not-related-->` from A suppresses the inferred `related` edge in both directions — same as `related` itself, which is bidirectional.

[Inference] The suppression is boolean, not graded. "These look similar but are not" reads as a categorical correction; partial credit ("they are 30% related") confuses the model and gives the author too many knobs.

## Syntax

[Inference] Two surfaces, identical storage — see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] for the full model:

- Inline wikilink: `[[docs/notes/foo.md]]<!--not-related-->`. Composes with ghost targets (`[[ghost/some-slug]]<!--not-related-->`) and pipe-alias.
- Frontmatter: `not-related: ["[[foo]]", "[[bar]]"]` — the key is the stereotype, each wikilink value a target. Each materializes one `mentions` edge plus one `edge_property` row keyed by `"stereotype"` with value `"not-related"`. A scalar `not-related: "[[foo]]"` declares a single target.

## Interaction with other stereotypes

`not-related` only affects inferred `related` edges. Authored alignments stand on their own:

- A wikilinks to B (bare mention) and A also says `[[B]]<!--not-related-->`. Both stand as separate property rows. The author has chosen to reference B in prose while also asserting that the topical-similarity inference is wrong. The mentions edge exists; two stereotype property rows attach to it (one bare, one `not-related`); the inferred related edge does not emit.
- A says `[[B]]<!--contradicts-->` and A says `[[B]]<!--not-related-->`. Both stand. The author disagrees with B and says the topic overlap is illusory. Reaching, but coherent — two stereotype property rows on the same edge.
- Neither stereotyped edge exists, MinHash would emit, no `not-related` mention exists. Inferred edge emits as today.

[Inference] No edge in the existing set affects what edges get stored. `not-related` introduces that capability indirectly — by being a mention, it triggers the existing mention-skip. The cost is paid once at reindex, not on every traversal.

## Open questions

- Default visibility in `relatives()`. Whether stereotyped mentions follow by default in a neighborhood walk is deferred to the expression-language redesign — see the parent note's open questions. A reasonable starting position: `not-related` mentions are visible in `via_edges` so the author's curation is auditable, but agents writing queries about "related neighbors" get the post-subtraction set by default.
- Audit affordance. Without a way to inspect which inferred edges were suppressed by `not-related` assertions, the author cannot tell whether the curation is doing the work they expect. The `export()` snapshot can carry both the stored edges and a separate "would-have-emitted" view, or `relatives` gains a debug mode. Defer until the basic mechanism works.
- Interaction with BM25 rerank. Once [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] lands, the set subtraction applies against BM25-scored candidates instead of MinHash-scored ones. The suppression mechanism is the same; the upstream score function changes.

## See also

- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — the parent design. Owns the stereotype model and the open-vocab policy.
- [[docs/notes/add-contradicts-as-an-authored-edge-kind.md]] — the rhetorical-negative sibling. Same syntax, different semantic category.
- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle that introduced the mention-skip pattern this stereotype rides on.
- [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — the upstream-score change this suppression composes with.
