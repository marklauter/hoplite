---
title: A property graph over an addressable corpus
summary: <todo: summary>
document:
  tags: [hoplite, graph, spec]
  created: 2026-05-29
---

# A property graph over an addressable corpus

<todo: introduction>

## Documents

A document is the graph's node — an addressable resource identified by its `uri`, a medium-agnostic, case-insensitive locator. A corpus document's uri is its repo-relative path (`docs/notes/foo.md`); `[[Docs/Foo.md]]` and `[[docs/foo.md]]` reach the same node because the uri collates case-insensitively.

Three variants, distinguished by whether the uri resolves to a real resource:

- Document — a real `.md` file on disk. `resolved = true`. Carries content fingerprints: an exact hash for change detection and a similarity sketch for near-duplicate discovery.
- Ghost — a wikilink target authored `[[ghost/<slug>]]` as an intentional open loop, awaiting its file. `resolved = false`. A synthetic `ghost` tag enumerates the corpus's open loops.
- URL — an external `http(s)` reference keyed by the verbatim URL. `resolved = false`, terminal, a synthetic `url` tag.

### Properties

A document carries its description as properties: typed key/value facts in entity-attribute-value form, one row per (document, key, value). They are the authored metadata — `tags`, `status`, `created`, and the open vocabulary beyond. A list-valued attribute fans out one row per element. Values store as text; `tags` casefold for case-insensitive lookup, other values store verbatim.

The key vocabulary is open: any key is accepted and stored as data, save the reserved words below. Keys are interned (see [Vocabulary](#vocabulary)) — a key string is stored once and referenced by integer from every property row that carries it.

Tags classify; properties carry state. A tag answers "what is this?" — immutable identity, the document's type and shape and domain. A mutable property answers "what state is it in?" Conflating them — a `draft` or `closed` tag — churns identity when the lifecycle moves. The full principle is in [[docs/notes/tags-classify-properties-carry-state.md]].

### Reserved words

Most keys are open vocabulary. A few are reserved: keys with a defined meaning and validation across the graph, regardless of which surface authors them. A reserved word is specified here, in the model: frontmatter carries the value, this document defines its meaning and validation.

- `created` — a creation timestamp. Prefers a full ISO date-time, and accepts a bare ISO date (`YYYY-MM-DD`) for backward compatibility with the corpus's authored dates. Optional; when absent, git history is the authoritative date.

The set is open and grows as keys earn defined semantics. Each reserved word names its type and validation rule here.

## Relationships

A relationship is the graph's edge — directed from `src` to `dst`, carrying a `kind` and a `confidence`. Kind is provenance, a closed enum of two — who asserted the edge:

- `declared` — the author asserted it, by writing a `[[wikilink]]` or markdown link in body text or naming it in frontmatter. `confidence` is `1.0`.
- `discovered` — the engine inferred it from a latent signal: content similarity, co-citation, temporal proximity, and the rest (the channels are in [[docs/hoplite/hoplite.md]]). `confidence` is the graded strength of the inference.

A relationship's *meaning* — citation, support, refutation — is a stereotype on the edge (see [Stereotypes](#stereotypes)). The destination's *nature* — document, ghost, or URL — is a fact about the node: a markdown link to an external site is a `declared` edge to a URL node, stereotyped `cites` when the author means citation.

At most one edge connects an ordered pair — `UNIQUE(src, dst)`, across both kinds. The two-pass build inserts declared edges first and discovered second; a declared edge wins the slot against a discovered collision.

An edge has a tail and a head, so the backlink — the inbound view — comes free. Symmetry is the stereotype's property: `supersedes` runs one way, a `related` or `not-related` tie reads both.

### Stereotypes

A stereotype is an open-vocabulary label on a declared edge — `cites`, `supports`, `supersedes`, `contradicts`, `not-related` — classifying what kind of link it is. Description takes a different shape on each side: a document carries an open key/value property vocabulary, an edge carries a label set.

A new stereotype extends the vocabulary as data, the way a new tag does; the parser accepts any label. The full model, the authoring surfaces, and the seed vocabulary are in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].

## Vocabulary

Two namespaces are interned: `property_key` holds the document-side property keys, `stereotype` holds the edge-side labels. Interning stores each string once and exposes the vocabulary as a readable set. That set is the Survey affordance — what an agent reads to learn which predicates compose before it queries the corpus.

Survey is the read graph's `match` shape applied to the schema: find and walk.

Find reads the namespace: `property_key` on the document side, `stereotype` on the edge side, each a small interned list.

Walk descends a key to its values — the distinct `value` rows under one `keyid`, served by the `(keyid, value)` reverse index. The keys are the nodes of a vocabulary graph, `key → value` the edge, the values the reachable set. A key's categorical-or-scalar nature resolves in the walk: a key reaching a handful of values is categorical — `tags`, `status`; one reaching thousands of near-unique values is scalar — a timestamp, a score. The distinction is empirical — the index carries the walk, and the agent reads it off the result.

Interning covers the find namespace: `property_key` interns document keys, `stereotype` interns edge labels, while walk-reached document values stay inline. The edge side has a single description dimension, so its survey is the find alone — a direct read of `stereotype`.

## Storage

The graph persists in SQLite, rebuilt by drop-and-recreate — the dominant cost is the bulk load, so the performance levers live in the loader. [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql) holds the tables, columns, indexes, and their rationale; the model maps to it directly: documents to `node`, relationships to `edge` (kinds interned in `edge_kind`), document properties to `node_property` (keys interned in `property_key`), edge stereotypes to `edge_stereotype` (labels interned in `stereotype`), the text projection to `fts`.
