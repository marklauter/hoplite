---
title: Contradicts stereotype marks authored disagreement
summary: contradicts is one of the v1 canonical stereotypes on the mentions edge — it labels a wikilink (or frontmatter edge entry) where the author argues against the target document. The negative-rhetorical signal grep cannot surface.
tags: [todo, edges, stereotypes, contradicts, design]
created: 2026-05-27
priority: low
effort: medium
status: open
---

# Contradicts stereotype marks authored disagreement

`contradicts` is one of the v1 canonical stereotypes on the `mentions` edge — it labels a wikilink (or frontmatter edge entry) where the author argues against the target document. The negative-rhetorical signal grep cannot surface.

## History

An earlier iteration of the edge model included `contradicts` as a distinct edge kind. It was dropped for day-one minimalism. The spec landed with the smallest viable edge set, and contradicts did not pull its weight against the cost of nailing down syntax and semantics under deadline.

Under the stereotype model in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]], contradicts no longer needs to be a separate edge kind. It rides on the existing `mentions` kind as an open-vocab label stored in `edge_property`. The original objection was that adding edge kinds is heavy. That objection no longer applies. Adding a stereotype is a parser-and-doc change only.

## Why the stereotype earns its place

Today's authored edge labels are uniformly positive in rhetoric. `mentions` says "see also." `cites` says "supporting evidence." Neither carries the agentic signal that a document is taking issue with another: superseding a prior decision, refuting a hypothesis, or disagreeing with a framing.

Two documents that contradict each other often look topically related to MinHash, because they share vocabulary when they engage with the same subject. They may or may not be wikilinked, depending on whether the author chose to reference the document being disagreed with. The relationship is real and load-bearing. Without an explicit signal the index cannot distinguish endorsement from rebuttal.

## Syntax

Two surfaces, identical storage. See [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] for the full model.

- Inline wikilink: `[[docs/notes/foo.md]]<!--contradicts-->`. Composes with ghost targets and pipe-alias.
- Frontmatter: `contradicts: ["[[foo]]", "[[bar]]"]` — the key is the stereotype, each wikilink value a target. Each materializes one edge plus one `edge_property` row keyed by `"stereotype"` with value `"contradicts"`. A scalar `contradicts: "[[foo]]"` asserts a single target.

## Open questions

- Confidence value. Authored, so `1.0` by parallel with `mentions` and `cites`. The contradicts stereotype is a categorical assertion, not a graded one.
- Reverse semantics. `direction=in` covers "who is contradicting me." No symmetric companion stereotype needed.
- Default visibility in `relatives()`. Whether stereotyped mentions follow by default in a neighborhood walk is deferred to the expression-language redesign — see the parent note's open questions.
- Mention-skip parity. Resolved under the stereotype model: any `(src, dst)` pair connected by a `mentions` edge — stereotyped or not — already skips the inferred `related` edge. The existing skip-set logic at `_emit_related_edges` does not change.

## See also

- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — the parent design. Owns the stereotype model and the open-vocab policy.
- [[docs/todos/add-not-related-as-a-structural-negative-edge-kind.md]] — the structural-negative sibling. Same syntax, different semantic category.
- [[docs/journal/2026-05-27-1845-related-edges-land-and-rank-replaces-threshold.md]] — the cycle that established the mention-skip pattern the contradicts stereotype inherits.
- [[docs/todos/rank-related-edges-by-bm25-cosine-not-minhash-jaccard.md]] — adjacent edge-quality work. Stereotypes are independent of how `related` confidence is scored.
