---
title: Schema
summary: "The SQLite schema for the Hoplite knowledge graph — an RDF-shaped triple store over a node dictionary: nodes, predicates, statement edges, the slot store backing the slot nodes, and FTS."
tags: [hoplite, schema, reference]
created: 2026-06-21
status: evolving
---

# Schema

The canonical SQLite schema for the Hoplite knowledge graph: an RDF-shaped triple store over a node dictionary, plus an FTS5 lexical index, rebuilt by drop-and-recreate. This spec is the source of truth; the importer's `schema.sql` mirrors it.

Every triple position holds a node; the middle is typed to the predicate facet. The model is [[docs/notes/every-triple-position-is-a-node.md]]; how it settled is [[docs/journal/2026-07-02-0139-the-reversal-every-triple-position-is-a-node.md]]; the term crosswalk is in [[docs/hoplite/glossary/README.md]]. The pre-reversal property-graph schema is preserved in git history.

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
  nodeid integer primary key references node(id),
  label text not null unique collate nocase
);

create table edge (
  src integer not null references node(id),
  predicateid integer not null references predicate(nodeid),
  dst integer not null references node(id),
  confidence real not null,
  primary key (src, predicateid, dst)
) without rowid;
create index idx_edge_dst on edge(dst, predicateid, src, confidence);
create index idx_edge_predicate on edge(predicateid, src, dst, confidence);

create table slot (
  predicateid integer not null references predicate(nodeid),
  nodeid integer not null references node(id),
  value,
  primary key (predicateid, nodeid)
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

Where the schema matches RDF:

- **The graph is a set of triples.** `edge`'s primary key enforces it: asserting the same triple twice yields one row, and multi-valued properties are repeated assertions.
- **Every term is a resource, predicates included.** Every term in every position is a node in the dictionary, addressed by uri; a predicate is a node carrying the [predicate facet](#predicate), so statements about the vocabulary are representable — stored as data, treated as data. Every node is named (RDF: no blank nodes): every uri derives from the corpus, so a rebuild reproduces the graph byte-identically.
- **`confidence` is the RDF-star annotation.** A statement about the statement — `<< src p dst >> hoplite:confidence n` — carried in-row: the triple's natural key makes every edge natively reified.
- **A statement is addressed by its terms.** A triple is identified by its three positions, in RDF and here alike (see [Addressing](#addressing)).

Where it deliberately diverges:

- **Values are nodes.** RDF puts values in a third term kind, the typed literal. Hoplite splits that role: an enumerable value becomes a **value node** (`status:locked` — a literal promoted to a SKOS-style concept, in Turtle's `prefix:localname` form), and freeform text or a blob becomes a **slot** (`summary:<doc-uri>` — the long-literal store, projected as a node on demand). A literal's datatype becomes a per-predicate fact if ever needed — a `datatype` column on `predicate`, matching `owl:DatatypeProperty`, declared once per predicate.
- **Closed world.** RDF assumes an open world, where absence means unknown. Hoplite's corpus is the entire world: the graph is a pure function of the files, rebuilt whole, so absence is knowable and insertion order can settle precedence.
- **Corpus-scoped names.** Uris are local names; the vault segment is the growth path to global identity (see [Addressing](#addressing)).

## Rebuild

The graph is rebuilt by drop-and-recreate — the dominant cost is the bulk load, and the biggest performance levers live in the loader:

- Load the whole rebuild inside a single transaction.
- During the rebuild, relax the durability pragmas — `journal_mode` and `synchronous` — since a crash just means re-running the rebuild.
- `foreign_keys` enforcement is OFF by default in SQLite. The `REFERENCES` clauses are free documentation unless enforcement is on; if it is, every insert pays a check the builder covers by constructing its data consistently. Decide deliberately.

## Addressing

Addresses are bare uris; the MCP tool layer is the resolver, taking a uri as a parameter. Matching is case-insensitive (`collate nocase` throughout).

Authoring and addressing are separate registers. Authors write bare wikilink targets (`[[docs/tag.md]]`), per the grammar in [[docs/hoplite/expressing-edges.md]]; the forms below are what the query and survey layer speaks. The register split is a standing rule, first drawn (in an older slash-rooted form) in [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]].

### Separators

Two separators split two naming authorities: **slash** joins path segments — the filesystem's namespace — and **colon** joins a predicate label to its operand — the vocabulary's namespace. The wikilink grammar keeps colons out of targets, so every document uri is colon-free and the two spaces are disjoint by construction. Colon addresses belong to the query layer; the form is Turtle's `prefix:localname` and the urn separator. The decision and its rejected alternatives (reserved roots, validation, `~` `#` `>>` `::` `\`) are recorded in [[docs/notes/colon-separates-vocabulary-addresses-from-paths.md]].

One label is **reserved**: `predicate`. An author-coined key so named would mint value uris (`predicate:tag`) that collide with predicate-node uris; the importer refuses or renames it. It is the vocabulary's only reserved word.

### Address kinds and resolution

Five stored kinds resolve with one dictionary seek on `node.uri`, falling through to `node_alias` on a miss:

- **document** — `docs/notes/foo.md`: a corpus path.
- **ghost** — `tag`: a corpus target named before its file exists.
- **url** — `https://...`: a scheme-carrying external reference.
- **value** — `status:locked`, `tag:note`, `created:2026-06-30`: the value lives in the address, so resolution completes at the dictionary — and the unique uri index doubles as a range index (`created:2026-06` is a prefix scan; ISO-8601 sorts lexicographically).
- **predicate** — `predicate:cites`: the vocabulary's own entries, nodes carrying the [predicate facet](#predicate).

One kind is projected on demand:

- **slot** — `summary:<doc-uri>`: the dictionary misses, so the resolver splits on the **first colon** (operands keep their own colons — `created:2026-06-30T21:34` parses fine; urls are stored, so they resolve at the dictionary before the parse) and runs three seeks: label → `predicateid`, tail → `nodeid` (aliases apply, so slot addresses survive renames), `(predicateid, nodeid)` → the value in the [slot store](#slot).

And one is addressed without a uri:

- **statements** — a triple is addressed by its three terms, consistent with RDF; its one annotation, `confidence`, rides in-row.

### In the query language

Turtle-shaped contexts — the query language — qualify every address: the leading colon at minimum (`:tag:note`). Turtle's first colon is the namespace boundary (a prefix contains letters only), so everything after it is the local name, where Turtle admits raw colons — the separator serializes unescaped. Qualification keeps predicate labels clear of declared prefixes: bare `tag:note` would read as prefix `tag`.

Hoplite's dialect relaxes strict `PN_LOCAL` in one way: raw `/` is allowed in local names — paths are just strings here; a strict-Turtle export escapes them (`\/`) or uses full-IRI form. The relaxation covers any character that is unambiguous mid-token — dots, dashes, slashes. Token delimiters stay out of reach: whitespace separates terms in every Turtle-shaped context, so `:status:in progress` is unwritable however permissive the dialect (open question 1).

### Cross-repo growth path

Uris are corpus-scoped local names. The vault segment (`<vault>/docs/foo.md` in the cross-repo model of [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]]) is the growth path to global identity: the vault plays the IRI authority, and a vault-qualified graph is the seed of an RDF named graph.

### Open questions

Held for the importer:

1. **Token-breaking characters in enumerable values.** `status: in progress` is categorical and wants to be a walkable value node, but whitespace ends a query-language term. Percent-encode, slugify at import, or a quoted-term form; undecided. Demoting to a slot loses the walkability that makes a categorical value worth interning.
2. **Anchors.** The wikilink grammar admits `doc#section` and `doc#^block` targets. Whether an anchored target earns its own node or resolves to the document's node is unresolved.
3. **The register form.** Documents are addressed by bare path today; a uniform kind-rooted register (`document:docs/tag.md`, `url:https://...`) would make every address self-describe its kind and turn resolver probing into pure namespace dispatch, at the cost of verbosity and a longer reserved-word list (`document`, `url` joining `predicate`). Bare-canonical stands until ruled.

## node

The node dictionary: one row per resource — the terms of every triple's subject and object positions. `id` is identity within the graph; `uri` is the external, medium-agnostic address. A node holds identity and nothing more; a resource's facts attach through statements.

Variants derive from the uri and the facets — the address and the rows carry the kind:

- **document** — a corpus uri with [slot](#slot) rows. The witness is `content_hash`, computed for every real file: bytes exist behind the node exactly when the hash slot does.
- **ghost** — a corpus uri named before its file exists; slot rows arrive when the file does.
- **url** — a scheme-carrying uri: an external resource.
- **value** — a vocabulary uri carrying its value in the address. Interned at first assertion and shared by every subject that asserts it — the sharing is what makes values walkable.
- **predicate** — a node with a [predicate facet](#predicate) row: the vocabulary's own entries, interned at first use in the middle position.

Slot nodes (`summary:<doc-uri>`, `title:<doc-uri>`, `minhash:<doc-uri>`) are projections: a slot address derives from subject + predicate, so the graph layer projects the node and its statement from the [slot store](#slot) on demand.

## node_alias

Alternate identities: additional uris that resolve to a node, asserted by the author — on rename, for example, so old wikilinks still reach the file. A resolution index: an alias is globally unique and maps to one node, so it is the primary key; the reverse index answers "what are node X's aliases?". It differs from `node.uri` only in that uri is the canonical identity.

Slot addresses inherit a document's aliases for free, since they embed its uri.

## predicate

The predicate facet: the registration that licenses a node for the middle position. A predicate is special by role — `doc-1 doc-2 doc-3` is three subjects in search of a verb, so the edge's middle column is typed to this table alone. The predicate term is a node like any other (uri `predicate:<label>`), so it also stands as a subject or object: statements about the vocabulary (`cites inverse-of cited-by`, `supersedes defined-by <doc>`) are stored as data and treated as data.

One flat open vocabulary: the former property keys (`tag`, `status`, `created`) and the edge labels (`cites`, `supports`, `supersedes`, `links-to`) are the same kind of thing, interned at first use in the middle position — a node row plus this facet row. The vocabulary is open and author-coined; surveying it is a scan of this table.

The facet repeats the derivation pattern: a document is a node with slot rows; a predicate is a node with a predicate row.

## edge

A statement — an RDF triple: subject, predicate, object, weighted by confidence. One row per triple; what the old model stored as one edge carrying a set of labels is several statements here. `confidence` is per-statement — the RDF-star annotation, carried in-row. An authored statement carries 1.0; an inferred one carries its inference score.

The triple is its own key: the primary key is the statement's identity, derived from the corpus and stable across rebuilds.

Two-pass build: asserted statements load first; inferred ones follow and collide out against the primary key. The author's word wins by insertion order, which is the whole provenance record.

Traversal indexes — the `WITHOUT ROWID` table is clustered on its primary key, so forward traversal (seek `src`, optionally narrowed by predicate, read `dst` and `confidence`) is covered by the table itself:

- `idx_edge_dst` — reverse traversal: seek `dst`, optionally narrowed by predicate, read `(src, confidence)`.
- `idx_edge_predicate` — predicate-led access: every statement carrying a predicate ("all cites edges", "all docs with a status"), covering `(src, dst, confidence)`.

## slot

The slot store: the long-literal half of the term dictionary, where a conventional triple store keeps the literals too large to intern. A value node carries its value in the address; a slot holds the values that outgrow one — freeform text (`title`, `summary`) and blobs (`content_hash`, `minhash`) — one row per subject per slot predicate.

The `PRIMARY KEY (predicateid, nodeid)` mirrors the address (`<predicate-label>:<node-uri>`) and enforces the functional constraint: one value per document per slot. Predicate-first clustering groups each predicate's values contiguously, so bulk sweeps — every `minhash` for near-duplicate inference, every `summary` for the FTS feed — are single range scans, while assembling one document's facet is a few exact seeks over the known slot predicates. The bare `value` column uses SQLite's per-row typing — text and blob coexist; a `datatype` column on `predicate` is the escape hatch if that proves too loose.

A new slot predicate is data: `title`, `summary`, and any future out-of-line predicate are rows here and in `predicate`.

Resolution of a slot uri is specified under [Addressing](#addressing); inside the database, a slot's address is the composite key `(predicateid, nodeid)` — derived from the corpus and stable across rebuilds.

`created` is an ordinary property — a statement to a value node like `created:2026-06-30` — so temporal ordering rides the node dictionary's uri index (see [Addressing](#addressing)).

## fts

Full-text search over each document's text projection (title, summary, body), powering ranked lexical search. `uri` is stored `UNINDEXED` only to tie a hit back to its node; the porter/unicode61 tokenizer gives stemmed matching. Title and summary feed from the slot store; body comes from the file at index time.

## Survey

Survey is match and walk over the graph proper: value nodes live in the dictionary and predicates in the facet, so surveying the vocabulary is a uri prefix scan plus a facet scan. The vocabulary is real rows — which is what retired the old namespace view.
