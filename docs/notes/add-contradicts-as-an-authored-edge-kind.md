---
title: Contradicts stereotype marks authored disagreement
summary: contradicts is one of the v1 canonical stereotypes on the mentions edge — it labels a wikilink (or frontmatter edge entry) where the author argues against the target document. The negative-rhetorical signal grep cannot surface.
document:
  tags: [note, hoplite, edges, stereotypes, contradicts, design, todo]
  created: 2026-05-27
  priority: low
  effort: medium
  status: open
---

# Contradicts stereotype marks authored disagreement

`contradicts` is one of the v1 canonical stereotypes on the `mentions` edge — it labels a wikilink (or frontmatter edge entry) where the author argues against the target document. The negative-rhetorical signal grep cannot surface.

## History

[Observation] An earlier iteration of the edge model included `contradicts` as a distinct edge kind. It was dropped for day-one minimalism — the spec landed with the smallest viable edge set, and contradicts did not pull its weight against the cost of nailing down syntax and semantics under deadline.

[Inference] Under the stereotype model in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]], contradicts no longer needs to be a separate edge kind. It rides on the existing `mentions` kind as an open-vocab label stored in `edge_property`. The original objection — adding edge kinds is heavy — no longer applies; adding a stereotype is a parser-and-doc change only.

## Why the stereotype earns its place

[Inference] Today's authored edge labels are uniformly positive in rhetoric. `mentions` says "see also." `cites` says "supporting evidence." Neither carries the agentic signal that a document is taking issue with another — superseding a prior decision, refuting a hypothesis, disagreeing with a framing.

[Inference] Two documents that contradict each other often look topically related to MinHash (they share vocabulary because they engage with the same subject) and may or may not be wikilinked, depending on whether the author chose to reference the document being disagreed with. The relationship is real and load-bearing, and without an explicit signal the index cannot distinguish endorsement from rebuttal.

## Syntax

[Inference] Two surfaces, identical storage — see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] for the full model:

- Inline wikilink: `[[contradicts:docs/notes/foo.md]]`. Composes with ghost targets and pipe-alias.
- Frontmatter: `edge.contradicts: [docs/notes/foo.md, docs/notes/bar.md]`. Each path materializes one edge plus one `edge_property` row keyed by `"stereotype"` with value `"contradicts"`. The equivalent nested form (`edge:` then `  contradicts: [...]`) parses identically.

## Open questions

- Confidence value. Authored, so `1.0` by parallel with `mentions` and `cites`. The contradicts stereotype is a categorical assertion, not a graded one.
- Reverse semantics. `direction=in` covers "who is contradicting me." No symmetric companion stereotype needed.
- Default visibility in `relatives()`. Whether stereotyped mentions follow by default in a neighborhood walk is deferred to the expression-language redesign — see the parent note's open questions.
- Mention-skip parity. Resolved under the stereotype model: any `(src, dst)` pair connected by a `mentions` edge — stereotyped or not — already skips the inferred `related` edge. The existing skip-set logic at `_emit_related_edges` does not change.

## See also

- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — the parent design. Owns the stereotype model and the open-vocab policy.
- [[docs/notes/add-not-related-as-a-structural-negative-edge-kind.md]] — the structural-negative sibling. Same syntax, different semantic category.
- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle that established the mention-skip pattern the contradicts stereotype inherits.
- [[docs/notes/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — adjacent edge-quality work. Stereotypes are independent of how `related` confidence is scored.
