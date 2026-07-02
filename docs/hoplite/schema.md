---
title: Schema
summary: "The SQLite schema for the Hoplite knowledge graph — an RDF-shaped triple store over a node dictionary: nodes, predicates, statement edges, the slot store backing the slot nodes, and FTS."
tags: [hoplite, schema, reference]
created: 2026-06-21
status: evolving
---

# Schema

The canonical SQLite schema for the Hoplite knowledge graph: an RDF-shaped triple store over a node dictionary, plus an FTS5 lexical index, rebuilt by drop-and-recreate. This spec is the source of truth — the importer's `schema.sql` mirrors it, never the other way around.

Every triple position is a node or a predicate: subject and object are nodes; the middle is a predicate. The model is [[docs/notes/every-triple-position-is-a-node.md]]; how it settled is [[docs/journal/2026-07-02-0139-the-reversal-every-triple-position-is-a-node.md]]; the term crosswalk is in [[docs/hoplite/glossary/README.md]]. The pre-reversal property-graph-shaped schema is preserved in git history.

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

## The RDF reading

The schema realizes RDF's model with a small set of deliberate divergences. Where it matches:

- **The graph is a set of triples.** An RDF graph is a set of statements; `edge`'s primary key enforces exactly that — asserting the same triple twice yields one row, and multi-valued properties are repeated assertions, never containers.
- **Subjects and objects are resources.** Every term in subject or object position is a node in the dictionary, addressed by uri. There are **no blank nodes**: every node's uri derives from the corpus, so every resource is named — a rebuild reproduces the graph byte-identically.
- **`confidence` is the RDF-star annotation.** A statement about the statement — `<< src p dst >> hoplite:confidence n` — carried in-row because the triple's natural key makes every edge natively reified. No reification quads, no annotation vocabulary.
- **A statement has no address of its own.** A triple is identified by its three terms, in RDF and here alike (see [Addressing](#addressing)).

Where it deliberately diverges:

- **There are no literals.** RDF puts values in a third term kind — the typed literal. Hoplite splits that role in two: an enumerable, slug-safe value becomes a **value node** (`status:locked` — RDF would call this promoting the literal to a SKOS concept, and the address is literally Turtle's `prefix:localname` form), and freeform text or a blob becomes a **slot** (`summary:<doc-uri>` — the long-literal store of a conventional triple store, projected as a node on demand). The datatype an RDF literal carries becomes a per-predicate fact if ever needed — a `datatype` column on `predicate`, matching `owl:DatatypeProperty`'s range — never a per-value tag.
- **Closed world.** RDF assumes an open world — absent statements are unknown, not false. Hoplite's corpus is the entire world: the graph is a pure function of the files, rebuilt whole, so absence is knowable and the two-pass build can let insertion order settle precedence.
- **Local names, not IRIs.** Uris are corpus-scoped. The vault segment (`node/<vault>/...` in the cross-repo model) is the growth path toward RDF's global identity — the vault plays the IRI authority, and a vault-qualified graph is the seed of a named graph — without adopting the http machinery.

## Rebuild

The graph is rebuilt by drop-and-recreate, never incrementally — so the dominant cost is the bulk load, and the biggest performance levers live in the loader, not the DDL:

- Load the whole rebuild inside a single transaction.
- During the rebuild, relax durability pragmas — `journal_mode` and `synchronous` — since a crash just means re-running the rebuild.
- `foreign_keys` enforcement is OFF by default in SQLite. The `REFERENCES` clauses are free documentation unless enforcement is enabled; if it is, every insert pays a check the builder doesn't need for data it constructs consistently itself. Decide deliberately whether to turn it on.

## Addressing

Addresses are bare uris — no scheme; the MCP tool layer is the resolver, taking a uri as a parameter. Matching is case-insensitive (`collate nocase` throughout).

Two separators split two naming authorities: **slash** joins path segments — the filesystem's namespace, per the wikilink grammar in [[docs/hoplite/expressing-edges.md]] — and **colon** joins a predicate label to its operand — the vocabulary's namespace. The wikilink grammar forbids colons in targets, so no document uri can contain one: the two spaces are disjoint by construction, and a vocabulary address can never collide with or shadow a document. (Colon addresses are query-layer addresses, never authored wikilinks; the form is Turtle's `prefix:localname` and the urn separator.)

Four kinds of address, three resolution paths:

- **Corpus and url uris** (`docs/notes/foo.md`, `https://...`) — one dictionary seek on `node.uri`, falling through to `node_alias` on a miss.
- **Value uris** (`status:locked`, `created:2026-06-30`) — the whole address is a dictionary key; same seek. The value lives in the address, so resolution never touches another table.
- **Slot uris** (`summary:<doc-uri>`) — never stored, so the dictionary misses; the resolver then splits on the **first colon** (the operand keeps its own colons — `created:2026-06-30T21:34` parses fine, and url operands are unreachable here because urls are stored and hit the dictionary) and runs three seeks: label → `predicateid`, tail → `nodeid` (aliases apply, so slot addresses survive renames), `(nodeid, predicateid)` → the value.
- **Statements** — no uri. A triple is addressed by its three terms, consistent with RDF; nothing in the model points at a statement, and `confidence` rides in-row.

Open questions, held for the importer:

1. **Predicates are not addressable.** In RDF a predicate is an IRI — a resource you can make statements about (`rdfs:domain`, `owl:inverseOf`). Hoplite's predicates live outside the dictionary, so a predicate cannot be a subject, and nothing links `predicate.label` to the glossary document that defines it. If statements about predicates are ever needed, the move is interning predicates into the dictionary; until then the glossary carries their definitions out-of-band.
2. **Categorical but not slug-safe values.** `status: in progress` is enumerable but doesn't fit the uri grammar — the value-node/slot line cracks. Slugify, encode, or demote to a slot; undecided.
3. **Anchors.** The wikilink grammar admits `doc#section` and `doc#^block` targets. Whether an anchored target earns its own node or resolves to the document's node is unresolved.

## node

The node dictionary: one row per resource — the terms of every triple's subject and object positions. `id` is identity within the graph; `uri` is the external, medium-agnostic address. A node holds identity and nothing more; a resource's facts attach through statements.

Variants are derived from the uri and the slot store, not flagged:

- **document** — a corpus uri with [slot](#slot) rows. The witness is `content_hash`: the importer computes it for every real file unconditionally, so bytes exist behind the node exactly when the hash slot does.
- **ghost** — a corpus uri with no slot rows: a dangling target, named before it is written.
- **url** — a scheme-carrying uri (`https://...`): an external resource.
- **value** — a vocabulary uri carrying its value in the address (`tag:note`, `status:locked`, `created:2026-06-30`). Interned at first assertion; shared by every subject that asserts it, which is what makes values walkable.

Slot nodes (`summary:<doc-uri>`, `title:<doc-uri>`, `minhash:<doc-uri>`) are **not** stored here. A slot address derives from subject + predicate, so the graph layer projects the node and its statement from the [slot store](#slot) on demand.

The unique uri index doubles as the value-range index: value uris embed their value, and ISO-8601 dates sort lexicographically, so a temporal range (`created > 2026-06`) is an ordinary prefix scan over `created:...` uris.

## node_alias

Alternate identities: additional uris that resolve to a node, asserted by the author (e.g. on rename, so old wikilinks still reach the file). A resolution index, not a description — an alias is globally unique and maps to one node, so it is the primary key; the reverse index answers "what are node X's aliases?". It differs from `node.uri` only in that uri is the canonical identity.

Slot addresses inherit a document's aliases for free, since they embed its uri.

## predicate

The interned vocabulary of predicates — the middle position of every triple, naming the relationship a statement asserts; RDF's predicate, kept in its own table rather than the dictionary (see [Addressing](#addressing), open question 1). One flat open vocabulary: the former property keys (`tag`, `status`, `created`) and the edge labels (`cites`, `supports`, `supersedes`, `links-to`) are the same kind of thing. The label is stored once and referenced by id; the vocabulary is glossary-governed, and surveying it is a scan of this table.

## edge

A statement — an RDF triple: subject, predicate, object, weighted by confidence. One row per triple; what the old model stored as one edge carrying a set of labels is several statements here. `confidence` is per-statement — the RDF-star annotation `<< src p dst >> hoplite:confidence n`, carried in-row. An authored statement carries 1.0; an inferred one carries its inference score.

No surrogate id: the natural key is the triple itself, which is also what makes every edge natively reified — the statement's identity is its terms.

Two-pass build: asserted statements load first; inferred ones follow and collide out against the primary key. The author's word wins by insertion order, so no per-statement provenance need be recorded.

Traversal indexes — the `WITHOUT ROWID` table is clustered on its primary key, so forward traversal (seek `src`, optionally narrowed by predicate, read `dst` and `confidence`) is covered by the table itself; no forward index needed:

- `idx_edge_dst` — reverse / "backtrack" traversal: seek `dst`, optionally narrowed by predicate, read `(src, confidence)`.
- `idx_edge_predicate` — predicate-led access: every statement carrying a predicate ("all cites edges", "all docs with a status"), covering `(src, dst, confidence)`.

## slot

The slot store: the long-literal half of the term dictionary — where a conventional triple store keeps the literals too large to intern. A value node carries its value in the address; a slot holds the values that don't fit one — freeform text (`title`, `summary`) and blobs (`content_hash`, `minhash`) — one row per subject per slot predicate. The `PRIMARY KEY (nodeid, predicateid)` is the functional constraint: one value per document per slot, enforced by the key rather than by column shape. The bare `value` column leans on SQLite's per-row typing — text and blob coexist; a `datatype` column on `predicate` is the escape hatch if that ever proves too loose.

A slot predicate is not a schema migration: `title`, `summary`, and any future out-of-line predicate are rows in `predicate` and rows here, never columns.

Resolution of a slot uri is specified under [Addressing](#addressing); inside the database, a slot's address is the composite key `(nodeid, predicateid)` — derived from the corpus, stable across rebuilds, no surrogate.

`created` is not a slot: an authored creation date is an ordinary property — a statement to a value node like `created:2026-06-30` — and temporal ordering rides the node dictionary's uri index (see [node](#node)).

## fts

Full-text search over each document's text projection (title, summary, body), powering ranked lexical search. `uri` is stored `UNINDEXED` only to tie a hit back to its node; the porter/unicode61 tokenizer gives stemmed matching. Title and summary feed from the slot store; body comes from the file at index time.

## No namespace view

The reversal made the vocabulary real: value nodes live in the node dictionary and predicates in their own table, so survey is a uri prefix scan plus a predicate scan — match and walk over the graph proper, not a projection kept beside it.
