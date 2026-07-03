---
title: Colon separates vocabulary addresses from paths
summary: "A vocabulary address is <predicate-label>:<operand> — priority:high, summary:docs/notes/foo.md — while slash remains the path separator. The wikilink grammar forbids colons in targets, so the vocabulary and filesystem namespaces are disjoint by construction; the collision between predicate labels and top-level folders dissolves without reserved roots or validation."
tags: [note, decision, hoplite, schema, addressing]
created: 2026-07-02
status: evolving
---

# Colon separates vocabulary addresses from paths

Two separators split two naming authorities. Slash joins path segments — the filesystem's namespace, per the wikilink grammar in [[docs/hoplite/expressing-edges.md]]. Colon joins a predicate label to its operand — the vocabulary's namespace: a value is `priority:high`, `tag:note`, `created:2026-06-30`; a literal projection is `summary:docs/notes/foo.md`. The grammar forbids colons in wikilink targets, so no document uri can contain one: a vocabulary address can never collide with or shadow a document, by construction.

The resolver splits on the first colon, so operands keep their own colons (`created:2026-06-30T21:34`). Urls also carry colons but are stored in the dictionary, and resolution is dictionary-first — only unstored addresses reach the colon parse, and those are literals. Specified in [[docs/hoplite/schema.md]]; the model is [[docs/notes/every-triple-position-is-a-node.md]].

The choice survives contact with Turtle, which the query language keeps. Turtle's first colon is the namespace boundary — a prefix cannot contain one — and its local names admit raw colons, so `:tag:note` tokenizes one way only: default prefix, local name `tag:note`, our separator intact and unescaped. The rule that makes it safe: in Turtle-shaped contexts an address is always namespace-qualified (the leading colon at minimum), never bare — bare `tag:note` would read as prefix `tag`. Hoplite's dialect relaxes strict `PN_LOCAL` to admit raw `/` in local names; a strict-Turtle export escapes the slashes or uses full-IRI form, a tax document paths pay under any separator.

## Alternatives

- **One flat slash-separated space.** The original form (`priority/high`, `summary/docs/notes/foo.md`). Rejected: predicate labels and top-level folder names both claim the first segment, and nothing coordinates the two authorities. A predicate named like a folder silently merges a value with a document (one dictionary key, two resources), and a folder named like a literal-valued predicate shadows every literal address behind it — no error either way.
- **Entity-rooted prefixes.** Reserve roots that mark the space — `node/tag/note`, `value/...`, `literal/...`. Works, but buys disjointness by spending address length and readability on every vocabulary uri, and the reserved words themselves become collision surface against future folders.
- **Importer validation.** Keep the flat space and reject any predicate whose label matches a top-level folder. Rejected: a standing tripwire, checked forever as the corpus and vocabulary evolve independently — and it breaks retroactively when an author creates a folder that collides with an established predicate.
- **A non-colon separator** (`~`, `#`, `>>`, `::`, `\`) — considered when keeping Turtle for the query language raised the prefix-homograph worry. Each fails: `#` is our anchor separator and the IRI fragment; `>>` closes an RDF-star quoted triple, which confidence uses; `::` is Dataview's inline-field marker and still contains colons; `\` is the escape character everywhere; and `~` needs the `\~` escape in Turtle local names — while colon is admitted raw. The grammar favors the separator we already had; the homograph is handled by the qualification rule instead.

## Why

The trade-off is serialization and linkability cost against structural safety.

- **It buys** disjointness that cannot fail: the collision is impossible rather than checked-against, with no reserved words, no validation pass, and no address bloat — the separator itself carries the namespace. It also reads as the standard's own notation: `priority:high` is a CURIE shape any RDF-literate reader parses on sight.
- **It costs** two things. Colon addresses can never be authored as wikilinks — correct today (they are query-layer addresses), but a constraint if value nodes ever want in-corpus linking. And it demands the qualification discipline: a bare `tag:note` in a Turtle context reads as prefix `tag`, so addresses must always carry their namespace (the leading colon at minimum). The serialization tax falls on document paths, not the separator — strict Turtle escapes the slashes — and Hoplite's own dialect simply allows them raw.
