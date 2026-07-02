---
title: Colon separates vocabulary addresses from paths
summary: "A vocabulary address is <predicate-label>:<operand> — status:locked, summary:docs/notes/foo.md — while slash remains the path separator. The wikilink grammar forbids colons in targets, so the vocabulary and filesystem namespaces are disjoint by construction; the collision between predicate labels and top-level folders dissolves without reserved roots or validation."
tags: [note, decision, hoplite, schema, addressing]
created: 2026-07-02
status: evolving
---

# Colon separates vocabulary addresses from paths

Two separators split two naming authorities. Slash joins path segments — the filesystem's namespace, per the wikilink grammar in [[docs/hoplite/expressing-edges.md]]. Colon joins a predicate label to its operand — the vocabulary's namespace: a value node is `status:locked`, `tag:note`, `created:2026-06-30`; a slot node is `summary:docs/notes/foo.md`. The grammar forbids colons in wikilink targets, so no document uri can contain one: a vocabulary address can never collide with or shadow a document, by construction.

The resolver splits on the first colon, so operands keep their own colons (`created:2026-06-30T21:34`). Urls also carry colons but are stored in the dictionary, and resolution is dictionary-first — only unstored addresses reach the colon parse, and those are slots. The form is Turtle's `prefix:localname` and the urn separator. Specified in [[docs/hoplite/schema.md]]; the model is [[docs/notes/every-triple-position-is-a-node.md]].

## Alternatives

- **One flat slash-separated space.** The original form (`status/locked`, `summary/docs/notes/foo.md`). Rejected: predicate labels and top-level folder names both claim the first segment, and nothing coordinates the two authorities. A predicate named like a folder silently merges a value node with a document (one dictionary key, two resources), and a folder named like a slot predicate shadows every slot address behind it — no error either way.
- **Entity-rooted prefixes.** Reserve roots that mark the space — `node/tag/note`, `value/...`, `slot/...`. Works, but buys disjointness by spending address length and readability on every vocabulary uri, and the reserved words themselves become collision surface against future folders.
- **Importer validation.** Keep the flat space and reject any predicate whose label matches a top-level folder. Rejected: a standing tripwire, checked forever as the corpus and vocabulary evolve independently — and it breaks retroactively when an author creates a folder that collides with an established predicate.

## Why

The trade-off is serialization and linkability cost against structural safety.

- **It buys** disjointness that cannot fail: the collision is impossible rather than checked-against, with no reserved words, no validation pass, and no address bloat — the separator itself carries the namespace. It also reads as the standard's own notation: `status:locked` is a CURIE shape any RDF-literate reader parses on sight.
- **It costs** two things. Colon addresses can never be authored as wikilinks — correct today (they are query-layer addresses), but a constraint if value nodes ever want in-corpus linking. And at the RDF serialization boundary, colons inside localnames need escaping or full-IRI form, so a future export of the graph to real Turtle pays a small ugliness tax.
