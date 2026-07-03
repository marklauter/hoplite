---
title: Schema
summary: "The SQLite schema for the Hoplite knowledge graph — an RDF-shaped triple store over a self-describing node dictionary: nodes in namespace chains grounded at meta:meta, statements, the literal store backing the literal nodes, and FTS."
tags: [hoplite, schema, reference]
created: 2026-06-21
status: evolving
---

# Schema

The canonical SQLite schema for the Hoplite knowledge graph: an RDF-shaped triple store over a self-describing node dictionary, plus an FTS5 lexical index, rebuilt by drop-and-recreate. This spec is the source of truth; the importer's `schema.sql` mirrors it.

Every position of a statement holds a node. Addresses are namespace chains grounded at `meta:meta`; edges and properties are the kinds licensed for the predicate position. The model is [[docs/notes/every-triple-position-is-a-node.md]]; how it settled is [[docs/journal/2026-07-02-0139-the-reversal-every-triple-position-is-a-node.md]]; the term crosswalk is in [[docs/hoplite/glossary/README.md]]. The pre-reversal property-graph schema is preserved in git history.

## DDL

```sql
create table node (
  id integer primary key,
  nsid integer not null references node(id),
  uri text not null collate nocase,
  unique (nsid, uri)
);
create index idx_node_uri on node(uri);

create table node_alias (
  alias text primary key collate nocase,
  nodeid integer not null references node(id)
) without rowid;
create index idx_node_alias on node_alias(nodeid);

create table statement (
  src integer not null references node(id),
  predicateid integer not null references node(id),
  dst integer not null references node(id),
  confidence real not null,
  primary key (src, predicateid, dst)
) without rowid;
create index idx_statement_dst on statement(dst, predicateid, src, confidence);
create index idx_statement_predicate on statement(predicateid, src, dst, confidence);

create table literal (
  predicateid integer not null references node(id),
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

How the schema realizes RDF:

- **The graph is a set of triples.** `statement`'s primary key enforces it: asserting the same triple twice yields one row, and multi-valued properties are repeated assertions — the idiom RDF itself prefers over its containers.
- **Every term is a resource.** Every term in every position is a node in the dictionary, addressed by its namespace chain. The predicate position is filled by an edge or property node, so statements about the vocabulary are representable — stored, never enforced. Every uri derives from the corpus, so every node is named (RDF: no blank nodes).
- **Values are resources.** RDF permits a value to be a resource, and its practice recommends it — "things, not strings." Hoplite makes it the rule: a value interns as a node (`priority:high`), and where a literal may only end a statement, a value node can begin one as well — described and walked like anything else. Bytes too large for an address live in the [literal](#literal) table behind a projected node (`summary:<doc-uri>`).
- **`confidence` is the RDF-star annotation.** A statement about the statement — `<< src p dst >> hoplite:confidence n` — carried in-row: the triple's natural key makes every statement natively reified.
- **A statement is addressed by its terms.** A triple is identified by its three positions, in RDF and here alike (see [Addressing](#addressing)).
- **Names are relative references.** Corpus and vocabulary names are relative — url nodes are already absolute — and RDF resolves relative references against a base. Assigning one (the vault, in the cross-repo model) makes identity global (see [Addressing](#addressing)).

## Rebuild

The graph is rebuilt by drop-and-recreate — the dominant cost is the bulk load, and the biggest performance levers live in the loader:

- Load the whole rebuild inside a single transaction.
- During the rebuild, relax the durability pragmas — `journal_mode` and `synchronous` — since a crash just means re-running the rebuild.
- `foreign_keys` enforcement is per-connection in SQLite; the importer turns it on, so the `REFERENCES` clauses are live constraints.

A rebuild is deterministic: every chain, node, statement, and literal key derives from the corpus alone, so rebuilding reproduces the graph byte-identically.

Two invariants live in the importer rather than the DDL, which cannot express them: only members of `edge` and `property` fill the predicate position (predicate-licensing is namespace-derived), and the namespace tree stays a tree grounded at `meta:meta`.

## Addressing

An address is a **namespace chain**: colon-joined names walking down from the root — `meta:property:priority:high` names the value `high` under the key `priority` under `property` under `meta`. Short forms abbreviate: any unique suffix resolves — `priority:high`, even bare `high` — the same shortest-unique discipline the wikilink grammar gives slugs. An ambiguous short form demands qualification; the importer warns when a newly coined name makes existing short forms ambiguous.

Addresses are bare strings — a scheme would be tool-api packaging, kept out of the model. The MCP tool layer is the resolver, taking an address as a parameter. Matching is case-insensitive (`collate nocase` throughout).

Authoring and addressing are separate registers. Authors write bare wikilink targets (`[[docs/tag.md]]`), per the grammar in [[docs/hoplite/expressing-edges.md]]; document-namespace nodes present bare the same way. The register split is a standing rule, first drawn (in an older slash-rooted form) in [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]].

### Separators

Two separators split two naming authorities: **slash** joins path segments inside a document uri — the filesystem's namespace — and **colon** joins the links of a chain — the vocabulary's. The wikilink grammar keeps colons out of targets, so a path can never collide with a chain. Colon addresses belong to the query layer; the form is Turtle's `prefix:localname` and the urn separator. The decision and its rejected alternatives are recorded in [[docs/notes/colon-separates-vocabulary-addresses-from-paths.md]].

### Address kinds and resolution

A fully qualified chain resolves link by link: each step is a seek on `unique (nsid, uri)`, starting from the `meta:meta` fixed point. A short form resolves on `idx_node_uri`: seek the final name, verify the given links upward, and a unique survivor wins. A colon-free address tries the document namespace first, falling through to `node_alias` — an alias is a flat authored string, colon-free by the wikilink grammar.

The stored kinds:

- **document** — `document:docs/notes/foo.md`, presented bare: a corpus path.
- **ghost** — a `document`-namespace node named before its file exists; literal rows arrive when the file does.
- **url** — `url:https://...`: an external reference, absolute already.
- **edge** — `edge:cites`: a pure relation, licensed for the predicate position.
- **property** — `property:priority`: a key, licensed for the predicate position; a value-routed key parents its values.
- **value** — `priority:high`, `tag:note`, `created:2026-06-30`: the value under its key. The `(nsid, uri)` index doubles as a per-key range index (`created:2026-06` is an ordered scan; ISO-8601 sorts lexicographically).

One kind is projected on demand:

- **literal** — `summary:<doc-uri>`: a literal-routed key parents no stored nodes, so the chain's last seek misses and the resolver projects instead — key → its `property` node, tail → `nodeid` (aliases apply, so literal addresses survive renames), `(predicateid, nodeid)` → the value in the [literal store](#literal).

And one is addressed without a name:

- **statements** — a triple is addressed by its three terms, consistent with RDF; its one annotation, `confidence`, rides in-row.

### In the query language

Turtle-shaped contexts — the query language — qualify every address: the leading colon at minimum (`:priority:high`). Turtle's first colon is the namespace boundary (a prefix cannot contain a colon), so everything after it is the local name, where Turtle admits raw colons — a whole chain serializes as one token, unescaped. Qualification keeps chain names clear of declared prefixes: bare `priority:high` would read as prefix `priority`.

Hoplite's dialect relaxes strict `PN_LOCAL` in one way: raw `/` is allowed in local names — paths are just strings here; a strict-Turtle export escapes them (`\/`) or uses full-IRI form. The relaxation covers any character that is unambiguous mid-token — dots, dashes, slashes. Token delimiters stay out of reach: whitespace separates terms in every Turtle-shaped context, so `:topic:property graphs` is unwritable however permissive the dialect (open question 1).

A query is a triple pattern that binds positions by chain address — `subject`, `predicate`, and `object` name the positions, not namespaces — and the unbound positions are the result: `(:predicate:status :object:todo)` returns every subject whose `status` is `todo`. The sketch is [[docs/notes/query-patterns-bind-positions-by-chain-address.md]].

### Cross-repo growth path

Corpus and vocabulary names are relative; url nodes are absolute. The vault segment (`<vault>/docs/foo.md` in the cross-repo model of [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]]) is the base that makes identity global: the vault plays the IRI authority, and a vault-qualified graph is the seed of an RDF named graph.

### Open questions

Held for the importer:

1. **Token-breaking characters in enumerable values.** `topic: property graphs` is categorical and wants to be a walkable value node, but whitespace ends a query-language term. Percent-encode, slugify at import, or a quoted-term form; undecided. Demoting to a literal loses the walkability that makes a categorical value worth interning.
2. **Anchors.** The wikilink grammar admits `doc#section` and `doc#^block` targets. Whether an anchored target earns its own node or resolves to the document's node is unresolved.
3. **Canonical presentation.** Tool output could present full chains, shortest-unique forms, or the bare register per kind; undecided beyond "documents present bare."
4. **One key, two routings.** Nothing yet forbids a key from both interning value nodes (`summary:draft`) and holding literal rows (`summary:<doc-uri>`); stored value nodes would shadow the literal projections. The likely rule is uniform routing — a key's objects are all value nodes or all literal rows — but it is unruled; until then the shadowing case is undefined.

## node

The node dictionary: one row per resource — every term of every statement. `id` is identity within the graph; `(nsid, uri)` is the address, presented by projection as the chain (see [Addressing](#addressing)). A node holds identity and nothing more; a resource's facts attach through statements.

The dictionary is self-describing: `nsid` references `node`, so namespaces are nodes, and a node is a namespace exactly when nodes live under it. The recursion grounds at one fixed point — `meta:meta`, whose `nsid` is its own id — and `meta` parents the four structural namespaces: `edge`, `property`, `document`, `url`. Keys parent their values; there is no namespace table and no name stored twice.

Kinds derive from namespace membership and the literal store — the chain and the rows carry the kind:

- **document** — a `document`-namespace node with [literal](#literal) rows. The witness is `content_hash`, computed for every real file: bytes exist behind the node exactly when the hash literal does.
- **ghost** — a `document`-namespace node named before its file exists.
- **url** — a `url`-namespace node: an external resource.
- **edge** — an `edge`-namespace node: a pure relation.
- **property** — a `property`-namespace node: a key. Value-routed keys parent their value nodes; literal-routed keys parent projections.
- **value** — a node under its key, the value as its uri. Interned at first assertion and shared by every subject that asserts it — the sharing is what makes values walkable.

Literal nodes (`summary:<doc-uri>`, `title:<doc-uri>`, `content_hash:<doc-uri>`, `minhash:<doc-uri>`) are projections: a literal address derives from key + subject, so the graph layer projects the node and its statement from the [literal store](#literal) on demand.

## node_alias

Alternate identities: additional names that resolve to a node, asserted by the author — on rename, for example, so old wikilinks still reach the file. A resolution index: an alias is globally unique and maps to one node, so it is the primary key; the reverse index answers "what are node X's aliases?". An alias is a flat authored string where the canonical identity is the `(nsid, uri)` pair — which is why the alias table earns its keep as its own resolution stage.

Literal addresses inherit a document's aliases for free, since they embed its uri.

## statement

A statement — an RDF triple: subject, predicate, object, weighted by confidence. One row per triple; what the old model stored as one edge carrying a set of labels is several statements here. `confidence` is per-statement — the RDF-star annotation, carried in-row. An authored statement carries 1.0; an inferred one carries its inference score.

`predicateid` holds an edge or property node — predicate-licensing is namespace-derived, maintained by the importer (see [Rebuild](#rebuild)); `src` and `dst` hold any node.

The triple is its own key: the primary key is the statement's identity, derived from the corpus and stable across rebuilds.

Two-pass build: asserted statements load first; inferred ones follow and collide out against the primary key. The author's word wins by insertion order, which is the whole provenance record.

Traversal indexes — the `WITHOUT ROWID` table is clustered on its primary key, so forward traversal (seek `src`, optionally narrowed by predicate, read `dst` and `confidence`) is covered by the table itself:

- `idx_statement_dst` — reverse traversal: seek `dst`, optionally narrowed by predicate, read `(src, confidence)`.
- `idx_statement_predicate` — predicate-led access: every statement carrying a predicate ("all cites statements", "all docs with a status"), covering `(src, dst, confidence)`.

## literal

The literal store: the long-literal half of the term dictionary, where a conventional triple store keeps the literals too large to intern. A value node carries its value in the address; a literal holds the values that outgrow one — freeform text (`title`, `summary`) and blobs (`content_hash`, `minhash`) — one row per subject per literal-routed key. (`created` sits on the value-node side of that line: the date rides the address, `created:2026-06-30`, and temporal ordering rides the dictionary's `(nsid, uri)` index — see [Addressing](#addressing).)

The `PRIMARY KEY (predicateid, nodeid)` mirrors the address (`<key>:<doc-uri>`) and enforces the functional constraint: one value per document per key. Predicate-first clustering groups each key's values contiguously, so bulk sweeps — every `minhash` for near-duplicate inference, every `summary` for the FTS feed — are single range scans, while assembling one document's facet is a few exact seeks over the known literal-routed keys. The bare `value` column uses SQLite's per-row typing — text and blob coexist; the escape hatch, if that proves too loose, is a per-key datatype fact.

A new literal-routed key is data: `title`, `summary`, and any future out-of-line key are rows here, plus the key's node under `property`.

Resolution of a literal address is specified under [Addressing](#addressing); inside the database, a literal's address is the composite key `(predicateid, nodeid)` — derived from the corpus and stable across rebuilds.

## fts

Full-text search over each document's text projection (title, summary, body), powering ranked lexical search. `uri` is stored `UNINDEXED` only to tie a hit back to its node; the porter/unicode61 tokenizer gives stemmed matching. Title and summary feed from the literal store; body comes from the file at index time.

## Survey

Survey is match and walk over the graph proper: the vocabulary is real rows in the dictionary, so surveying keys and relations is a scan under `property` and `edge`, and surveying a key's values is a scan under the key — ordered seeks on the `(nsid, uri)` index, real interned rows where the old schema computed a view.
