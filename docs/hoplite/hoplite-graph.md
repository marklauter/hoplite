---
title: A property graph over an addressable corpus
summary: <todo: summary>
tags: [hoplite, graph, spec]
created: 2026-05-29
---

# A property graph over an addressable corpus

<todo: introduction>

## Documents

A document is the graph's node.

- `id` — internal integer key (storage only)
- `uri` — identity; medium-agnostic, case-insensitive locator
- `resolved` — whether the uri backs a real resource (document) or dangles (ghost, URL)
- `content_hash` — exact fingerprint, for change detection
- `minhash` — similarity sketch, for near-duplicate discovery
- `created` — authored creation timestamp
- `title` — first-class description attribute
- `summary` — first-class description attribute
- tags — classification label set
- properties — open key/value description
- aliases — alternate identities that resolve to the node

### Identity

A document's `uri` is its identity — a medium-agnostic, case-insensitive locator. A corpus document's uri is its repo-relative path (`docs/notes/foo.md`); `[[Docs/Foo.md]]` and `[[docs/foo.md]]` reach the same node because the uri collates case-insensitively.

### Variants

`resolved` marks whether the uri backs a real resource. Three variants follow:

- Document — a real `.md` file on disk. `resolved = true`.
- Ghost — a wikilink target authored `[[ghost/<slug>]]` as an intentional open loop, awaiting its file. `resolved = false`. A synthetic `ghost` tag enumerates the corpus's open loops.
- URL — an external `http(s)` reference keyed by the verbatim URL. `resolved = false`, terminal, a synthetic `url` tag.

### Fingerprints

A resolved document carries two fingerprints of its bytes: `content_hash`, an exact hash for change detection, and `minhash`, a similarity sketch for near-duplicate discovery. Ghost and URL nodes are byteless.

### Created

`created` is the authored creation timestamp — a scalar fact, so a column on `node` rather than a property. Optional; when absent, git history is the authoritative date.

### Title and summary

`title` and `summary` are first-class description attributes, asserted by the author. The title names the document beyond its filename; the summary is its lede — the gist a reader scans before opening the file. Every document asserts one of each. Their canonical store is the `fts` text projection (title, summary, body), not a `node` column; the model treats them as first-class attributes regardless of where they reify.

### Tags

A document's classification: an open-vocabulary set of labels (`note`, `journal`, `design`). Tags is the node-side counterpart to edge stereotypes — a label set, not a key/value property — so its labels intern in `tag` and attach through the `node_tag` junction. The walker injects synthetic `ghost` and `url` tags, so those node variants enumerate like any other.

Tags classify; properties carry state. A tag answers "what is this?" — immutable identity, the document's type and shape and domain. A mutable property answers "what state is it in?" Conflating them — a `draft` or `closed` tag — churns identity when the lifecycle moves. The full principle is in [[docs/notes/tags-classify-properties-carry-state.md]].

### Properties

Beyond the attributes above, a document carries open-ended description as properties — typed key/value facts in entity-attribute-value form, stored across two tables:

- `node_property` — one row per (document, key, value)
- `property_key` — the interned key vocabulary (see [Vocabulary](#vocabulary))

Properties hold open vocabulary only: author-coined keys with no model-defined meaning. A key whose meaning the model fixes earns its own structure instead — a scalar becomes a column (`created`), a classification becomes the tag label set, an alternate identity becomes the alias index — so `node_property` stays purely open. A list-valued attribute fans out one row per element, values store as text, and a key string is interned once in `property_key` and referenced by integer from every row that carries it.

### Aliases

Alternate uris that resolve to the node, declared by the author — e.g. on rename, so old wikilinks still reach the file. A resolution index (`node_alias`), not a description: an alias is globally unique and maps to one node, differing from `uri` only in that uri is the canonical identity.

## Relationships

A relationship is the graph's edge.

- `id` — internal integer key (storage only)
- `src` — source node
- `dst` — destination node
- `kind` — provenance: `declared` or `discovered`
- `confidence` — graded strength of the tie
- stereotypes — open-vocabulary labels describing the link

### Direction

`src` and `dst` are the edge's endpoints — directed, tail to head. The backlink — the inbound view — comes free. Symmetry is the stereotype's property: `supersedes` runs one way, a `related` or `not-related` tie reads both. The destination's nature — document, ghost, or URL — is the node's fact: a markdown link to an external site is a `declared` edge to a URL node.

### Kind

`kind` is provenance, a closed enum of two — who asserted the edge:

- `declared` — the author asserted it, by writing a `[[wikilink]]` or markdown link in body text or naming it in frontmatter.
- `discovered` — the engine inferred it from a latent signal: content similarity, co-citation, temporal proximity, and the rest (the channels are in [[docs/hoplite/hoplite.md]]).

### Confidence

Confidence follows kind: a `declared` edge is `1.0`, a `discovered` edge carries the graded strength of the inference.

### Uniqueness

At most one edge connects an ordered pair — `UNIQUE(src, dst)`, across both kinds. The two-pass build inserts declared edges first and discovered second; a declared edge wins the slot against a discovered collision.

### Stereotypes

A relationship's meaning — citation, support, refutation — is a stereotype: an open-vocabulary label on a declared edge — `cites`, `supports`, `supersedes`, `contradicts`, `not-related` — classifying what kind of link it is. An edge's stereotypes are stored across two tables:

- `edge_stereotype` — the junction, a set of labels per edge
- `stereotype` — the interned label vocabulary (see [Vocabulary](#vocabulary))

Description takes a different shape on each side: a document carries an open key/value property vocabulary, an edge carries a label set. A new stereotype extends the vocabulary as data, the way a new tag does; the parser accepts any label. The full model, the authoring surfaces, and the seed vocabulary are in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].

## Vocabulary

The find-namespace is interned in two tables, one per side of the graph:

- `property_key` — the document-side property keys
- `stereotype` — the edge-side labels

Each holds the same `(id, string)` shape: a surrogate id and the interned string, unique and case-insensitive. Interning stores each string once and exposes the vocabulary as a readable set. That set is the Survey affordance — what an agent reads to learn which predicates compose before it queries the corpus.

Survey is the read graph's `match` shape applied to the schema: find and walk.

Find reads the namespace: `property_key` on the document side, `stereotype` on the edge side, each a small interned list.

Walk descends a key to its values — the distinct `value` rows under one `keyid`, served by the `(keyid, value)` reverse index. The keys are the nodes of a vocabulary graph, `key → value` the edge, the values the reachable set. A key's categorical-or-scalar nature resolves in the walk: a key reaching a handful of values is categorical — `tags`, `status`; one reaching thousands of near-unique values is scalar — a timestamp, a score. The distinction is empirical — the index carries the walk, and the agent reads it off the result.

Interning covers the find namespace: `property_key` interns document keys, `stereotype` interns edge labels, while walk-reached document values stay inline. The edge side has a single description dimension, so its survey is the find alone — a direct read of `stereotype`.

## Storage

The graph persists in SQLite, rebuilt by drop-and-recreate — the dominant cost is the bulk load, so the performance levers live in the loader. [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql) holds the tables, columns, indexes, and their rationale; the model maps to it directly: documents to `node`, relationships to `edge` (kinds interned in `edge_kind`), document properties to `node_property` (keys interned in `property_key`), edge stereotypes to `edge_stereotype` (labels interned in `stereotype`), the text projection to `fts`.
