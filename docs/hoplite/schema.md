---
title: Schema
summary: "The SQLite schema for the Hoplite knowledge graph — a triple store over a node dictionary: nodes, predicates, statement edges, the slot store backing the slot nodes, and FTS."
tags: [hoplite, schema, reference]
created: 2026-06-21
status: evolving
---

# Schema

The canonical SQLite schema for the Hoplite knowledge graph: a triple store over a node dictionary, plus an FTS5 lexical index, rebuilt by drop-and-recreate. This spec is the source of truth — the importer's `schema.sql` mirrors it, never the other way around.

Every triple position is a node or a predicate: subject and object are nodes; the middle is a predicate. The model is [[docs/notes/every-triple-position-is-a-node.md]]; how it settled is [[docs/journal/2026-07-02-0139-the-reversal-every-triple-position-is-a-node.md]]. The pre-reversal property-graph-shaped schema is preserved in git history.

## DDL

```sql
create table node (
  id integer primary key,
  uri text not null unique collate nocase
);

create table node_alias (
  alias text primary key collate nocase,
  nodeid integer not null references node(id)
) without rowid;
create index idx_node_alias on node_alias(nodeid);

create table predicate (
  id integer primary key,
  label text not null unique collate nocase
);

create table edge (
  src integer not null references node(id),
  predicateid integer not null references predicate(id),
  dst integer not null references node(id),
  confidence real not null,
  primary key (src, predicateid, dst)
) without rowid;
create index idx_edge_dst on edge(dst, predicateid, src, confidence);
create index idx_edge_predicate on edge(predicateid, src, dst, confidence);

create table slot (
  nodeid integer not null references node(id),
  predicateid integer not null references predicate(id),
  value,
  primary key (nodeid, predicateid)
) without rowid;

create virtual table fts using fts5(
  uri unindexed,
  title,
  summary,
  body,
  tokenize = 'porter unicode61',
  detail = 'column'
);
```

## Rebuild

The graph is rebuilt by drop-and-recreate, never incrementally — so the dominant cost is the bulk load, and the biggest performance levers live in the loader, not the DDL:

- Load the whole rebuild inside a single transaction.
- During the rebuild, relax durability pragmas — `journal_mode` and `synchronous` — since a crash just means re-running the rebuild.
- `foreign_keys` enforcement is OFF by default in SQLite. The `REFERENCES` clauses are free documentation unless enforcement is enabled; if it is, every insert pays a check the builder doesn't need for data it constructs consistently itself. Decide deliberately whether to turn it on.

The graph is a pure function of the corpus: every node uri, every statement, and every slot key derives from file content, never from load order. Nothing carries a surrogate address — a rebuild reproduces the graph byte-identically.

## node

The node dictionary: one row per addressable resource — the graph's vertices and the terms of every triple's subject and object positions. `id` is identity within the graph; `uri` is the external, medium-agnostic address. A node holds identity and nothing more; a resource's facts attach through statements.

Variants are derived from the uri and the slot store, not flagged:

- **document** — a corpus uri with [slot](#slot) rows. The witness is `content_hash`: the importer computes it for every real file unconditionally, so bytes exist behind the node exactly when the hash slot does.
- **ghost** — a corpus uri with no slot rows: a dangling target, named before it is written.
- **url** — a scheme-carrying uri (`https://...`): an external resource.
- **value** — a vocabulary uri carrying its value in the address (`tag/note`, `status/locked`, `created/2026-06-30`). Interned at first assertion; shared by every subject that asserts it, which is what makes values walkable.

Slot nodes (`summary/<doc-uri>`, `title/<doc-uri>`, `minhash/<doc-uri>`) are **not** stored here. A slot address derives from subject + predicate, so the graph layer projects the node and its statement from the [slot store](#slot) on demand.

The unique uri index doubles as the value-range index: value uris embed their value, and ISO-8601 dates sort lexicographically, so a temporal range (`created > 2026-06`) is an ordinary prefix scan over `created/...` uris.

Open question: value namespaces are rooted by predicate labels, so a predicate coined with the same label as a top-level corpus folder would collide with document uris. Resolve when the importer lands; entity-rooted forms (`node/tag/note`) are the fallback.

## node_alias

Alternate identities: additional uris that resolve to a node, asserted by the author (e.g. on rename, so old wikilinks still reach the file). A resolution index, not a description — an alias is globally unique and maps to one node, so it is the primary key; the reverse index answers "what are node X's aliases?". It differs from `node.uri` only in that uri is the canonical identity.

Slot addresses inherit a document's aliases for free, since they embed its uri.

## predicate

The interned vocabulary of predicates — the middle position of every triple, naming the relationship a statement asserts. One flat open vocabulary: the former property keys (`tag`, `status`, `created`) and the edge labels (`cites`, `supports`, `supersedes`, `links-to`) are the same kind of thing. The label is stored once and referenced by id; the vocabulary is glossary-governed, and surveying it is a scan of this table.

## edge

A statement: subject — predicate — object, weighted by confidence. One row per triple; what the old model stored as one edge carrying a set of labels is several statements here. `confidence` is per-statement — the natively reified "statement about the statement" (RDF-star: `<< src p dst >> hoplite:confidence n`). An authored statement carries 1.0; an inferred one carries its inference score.

No surrogate id: with the predicate in-row there is no junction left to key, and the natural key is the triple itself.

Two-pass build: asserted statements load first; inferred ones follow and collide out against the primary key. The author's word wins by insertion order, so no per-statement provenance need be recorded.

Traversal indexes — the `WITHOUT ROWID` table is clustered on its primary key, so forward traversal (seek `src`, optionally narrowed by predicate, read `dst` and `confidence`) is covered by the table itself; no forward index needed:

- `idx_edge_dst` — reverse / "backtrack" traversal: seek `dst`, optionally narrowed by predicate, read `(src, confidence)`.
- `idx_edge_predicate` — predicate-led access: every statement carrying a predicate ("all cites edges", "all docs with a status"), covering `(src, dst, confidence)`.

## slot

The slot store: the long-value half of the term dictionary. Where a value node carries its value in the address, a slot holds the values that don't fit one — freeform text (`title`, `summary`) and blobs (`content_hash`, `minhash`) — one row per subject per slot predicate. The `PRIMARY KEY (nodeid, predicateid)` is the functional constraint: one value per document per slot, enforced by the key rather than by column shape. The bare `value` column leans on SQLite's per-row typing — text and blob coexist; a datatype tag column is the escape hatch if that ever proves too loose.

A slot predicate is not a schema migration: `title`, `summary`, and any future out-of-line predicate are rows in `predicate` and rows here, never columns.

Addressing — a slot's uri is `<predicate-label>/<subject-uri>` (`summary/docs/notes/foo.md`). The parse is unambiguous: a predicate label is a single slug segment, so the resolver splits on the first slash. Resolution is three index seeks:

1. head → `predicate.label` → `predicateid`.
2. tail → `node.uri` → `nodeid`, falling through to `node_alias` on a miss — so slot addresses survive renames for free.
3. `(nodeid, predicateid)` → the clustered primary key here → the value.

Shared value nodes and slot nodes share the `<predicate>/<tail>` surface. The resolver distinguishes them by where they live: value nodes are stored in the dictionary, slot nodes never are — so resolution probes `node.uri` for the whole address first; a hit is a value node, a miss parses the slot. Inside the database, a slot's address is the composite key `(nodeid, predicateid)`: derived from the corpus, stable across rebuilds, no surrogate.

`created` is not a slot: an authored creation date is an ordinary property — a statement to a value node like `created/2026-06-30` — and temporal ordering rides the node dictionary's uri index (see [node](#node)).

## fts

Full-text search over each document's text projection (title, summary, body), powering ranked lexical search. `uri` is stored `UNINDEXED` only to tie a hit back to its node; the porter/unicode61 tokenizer gives stemmed matching. Title and summary feed from the slot store; body comes from the file at index time.

## No namespace view

The reversal made the vocabulary real: value nodes live in the node dictionary and predicates in their own table, so survey is a uri prefix scan plus a predicate scan — match and walk over the graph proper, not a projection kept beside it.
