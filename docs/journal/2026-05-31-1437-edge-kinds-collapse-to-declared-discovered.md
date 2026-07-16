---
title: Edge kinds collapse to declared and discovered
summary: The three-kind edge enum (mentions, cites, related) conflated provenance, relationship-meaning, and target-type. Collapsed to two kinds by provenance — declared and discovered — moving meaning to open-vocab stereotypes and target-type to the destination node. Supersedes the cites-as-kind decision.
tags: [journal, hoplite, graph, edges, decision]
created: 2026-05-31
---

# Edge kinds collapse to declared and discovered

Going in, the graph carried a closed enum of three edge kinds — `mentions` (wikilink, doc→doc), `cites` (markdown link, doc→URL), `related` (MinHash similarity). Designing the apex overview ([[docs/specs/hoplite.md]]) forced the question of what an agent actually declares, and the enum didn't survive it.

## the problem

The three kinds sorted on three different axes at once, and only one of them is "kind":

- `cites` conflated a target-type fact (the destination is a URL node) with a meaning (citation). A markdown link can be a citation, a "see also," or a refutation — exactly like a wikilink. Neither target-type nor meaning is edge-kind.
- `mentions` was a declared link with no stated meaning — the absence of a stereotype, not a kind.
- `related` was the same on the inferred side.

Strip meaning and target-type out, and the only thing left distinguishing edges is provenance: the author asserted it, or the engine inferred it.

## decision

Two kinds, by provenance: `declared` (asserted, confidence 1.0) and `discovered` (inferred, graded). This makes the edge model identical to the authored/emergent channel spine in [[docs/notes/relatedness-signals.md]], and the affordance verbs name the output — declare produces a declared edge, discover produces a discovered one.

Everything the old enum carried relocates:

- meaning → an open-vocabulary stereotype in `edge_property` (`cites`, `supports`, `contradicts`); a bare edge is just a link. See [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].
- target-type → the destination node, through the existing `resolved` flag and synthetic `url`/`ghost` tags.
- confidence → follows kind: declared `1.0`, discovered graded.

`UNIQUE(src, dst)` and the two-pass build stay, and simplify: pass one inserts declared, pass two discovered, declared wins the slot. "Authored beats inferred" is now literally "declared beats discovered."

This supersedes the `cites`-as-kind decision in [[docs/journal/2026-05-27-1600-external-links-cites-edges-and-proxies.md]] — citation is a stereotype now, not a kind.

## outcome

Captured at the model layer: the canon ([[docs/specs/hoplite-graph.md]]), the architecture and tool-api docs, the skill component (rebuilt into the research, taking-notes, and journaling skills), the stereotypes note, and `schema.sql` comments all state the two-kind model. No DDL changed — `edge_kind` interns two values instead of three, and the kind-leading indexes work unchanged.

## next

The behavioral code is deferred to the in-flight SQLite walker rewrite, where it lands as one coupled unit: the walker emits `declared`/`discovered` and seeds `edge_kind`; stereotype population wires `frontmatter.edge_stereotypes()` into the walker so a markdown link becomes a declared edge to a URL node; `tools.py` swaps `_ALWAYS_FOLLOW` to `{declared}` and renames `top_k_related` → `top_k_discovered`; the kind-asserting tests update to the new values.
