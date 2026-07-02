---
title: Schema
summary: "The SQLite schema for the Hoplite knowledge graph — an RDF-shaped triple store over a node dictionary: namespaces and nodes, the predicate registration, statement edges, the literal store backing the literal nodes, and FTS."
tags: [hoplite, schema, reference]
created: 2026-06-21
status: evolving
---

# Schema

The canonical SQLite schema for the Hoplite knowledge graph: an RDF-shaped triple store over a node dictionary, plus an FTS5 lexical index, rebuilt by drop-and-recreate. This spec is the source of truth; the importer's `schema.sql` mirrors it.

Every triple position holds a node; the middle is typed to the predicate registration. The model is [[docs/notes/every-triple-position-is-a-node.md]]; how it settled is [[docs/journal/2026-07-02-0139-the-reversal-every-triple-position-is-a-node.md]]; the term crosswalk is in [[docs/hoplite/glossary/README.md]]. The pre-reversal property-graph schema is preserved in git history.

## DDL

```sql
create table namespace (
  id integer primary key,
  name text not null unique collate nocase
);

create table node (
  id integer primary key,
  nsid integer not null references namespace(id),
  uri text not null collate nocase,
  unique (nsid, uri)
);

create table node_alias (
  alias text primary key collate nocase,
  nodeid integer not null references node(id)
) without rowid;
create index idx_node_alias on node_alias(nodeid);

create table predicate (
  nodeid integer primary key references node(id)
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

create table literal (
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

How the schema realizes RDF:

- **The graph is a set of triples.** `edge`'s primary key enforces it: asserting the same triple twice yields one row, and multi-valued properties are repeated assertions — the idiom RDF itself prefers over its containers.
- **Every term is a resource, predicates included.** Every term in every position is a node in the dictionary, addressed by uri; a predicate is a node carrying the [predicate registration](#predicate), so statements about the vocabulary are representable — stored, never enforced. Every uri derives from the corpus, so every node is named (RDF: no blank nodes).
- **Values are resources.** RDF permits a value to be a resource, and its practice recommends it — "things, not strings." Hoplite makes it the rule: a value interns as a node (`priority:high`), and where a literal may only end a statement, a value node can begin one as well — described and walked like anything else. Bytes too large for an address live in the [literal](#literal) table behind a projected node (`summary:<doc-uri>`).
- **`confidence` is the RDF-star annotation.** A statement about the statement — `<< src p dst >> hoplite:confidence n` — carried in-row: the triple's natural key makes every edge natively reified.
- **A statement is addressed by its terms.** A triple is identified by its three positions, in RDF and here alike (see [Addressing](#addressing)).
- **Names are relative references.** Corpus and vocabulary uris are relative names — url nodes are already absolute — and RDF resolves relative references against a base. Assigning one (the vault, in the cross-repo model) makes identity global (see [Addressing](#addressing)).

## Rebuild

The graph is rebuilt by drop-and-recreate — the dominant cost is the bulk load, and the biggest performance levers live in the loader:

- Load the whole rebuild inside a single transaction.
- During the rebuild, relax the durability pragmas — `journal_mode` and `synchronous` — since a crash just means re-running the rebuild.
- `foreign_keys` enforcement is per-connection in SQLite; the importer turns it on, so the `REFERENCES` clauses are live constraints.

A rebuild is deterministic: every namespace, node, statement, and literal key derives from the corpus alone, so rebuilding reproduces the graph byte-identically.

## Addressing

Addresses are bare uris; a scheme would be tool-api packaging, kept out of the model. The MCP tool layer is the resolver, taking a uri as a parameter. Matching is case-insensitive (`collate nocase` throughout).

Storage splits an address in two: a [namespace](#namespace) and a uri, `unique (nsid, uri)`. The presented address is a projection over the pair — a vocabulary namespace prefixes its name and a colon to the uri; the `document` and `url` namespaces present the uri alone.

Authoring and addressing are separate registers. Authors write bare wikilink targets (`[[docs/tag.md]]`), per the grammar in [[docs/hoplite/expressing-edges.md]]; the forms below are what the query and survey layer speaks. The register split is a standing rule, first drawn (in an older slash-rooted form) in [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]].

### Separators

Two separators split two naming authorities: **slash** joins path segments — the filesystem's namespace — and **colon** joins a predicate label to its operand — the vocabulary's namespace. The wikilink grammar keeps colons out of targets, so every document uri is colon-free and the two spaces are disjoint by construction. Colon addresses belong to the query layer; the form is Turtle's `prefix:localname` and the urn separator. The decision and its rejected alternatives (reserved roots, validation, `~` `#` `>>` `::` `\`) are recorded in [[docs/notes/colon-separates-vocabulary-addresses-from-paths.md]].

Three names are **reserved**: `document`, `url`, and `predicate` — the structural namespaces. An author-coined key so named would mint value nodes inside them, colliding with paths, urls, or the vocabulary's own entries. Interning is get-or-create, so uniqueness refuses nothing; the importer checks author-coined keys against the reserved list explicitly and refuses or renames — an implementation detail captured here until the importer owns it.

### Address kinds and resolution

Resolution dispatches on shape. A colon-free address seeks `(document, local)`, falling through to `node_alias` — an alias is authored under the wikilink grammar, so it never contains a colon. A colon-bearing address seeks `(url, address)` whole, then splits on the **first colon** (operands keep their own colons — `created:2026-06-30T21:34` parses fine) and seeks `(namespace, local)`. Five stored kinds resolve on those seeks:

- **document** — `docs/notes/foo.md`: `(document, <path>)`.
- **ghost** — `tag`: `(document, <target>)`, named before its file exists.
- **url** — `https://...`: `(url, <address>)`, an external reference.
- **value** — `priority:high`, `tag:note`, `created:2026-06-30`: `(<label>, <value>)` — the value lives in the address, so resolution completes at the dictionary, and the `(nsid, uri)` index doubles as a per-namespace range index (`created:2026-06` is an ordered scan; ISO-8601 sorts lexicographically).
- **predicate** — `predicate:cites`: `(predicate, <label>)`, carrying the [predicate registration](#predicate).

One kind is projected on demand:

- **literal** — `summary:<doc-uri>`: every stored seek misses (literal-valued labels claim no namespace row), so the resolver runs three seeks: label → `(predicate, <label>)` and its registration, tail → `nodeid` (aliases apply, so literal addresses survive renames), `(predicateid, nodeid)` → the value in the [literal store](#literal).

And one is addressed without a uri:

- **statements** — a triple is addressed by its three terms, consistent with RDF; its one annotation, `confidence`, rides in-row.

### In the query language

Turtle-shaped contexts — the query language — qualify every address: the leading colon at minimum (`:tag:note`). Turtle's first colon is the namespace boundary (a prefix cannot contain a colon), so everything after it is the local name, where Turtle admits raw colons — the separator serializes unescaped. Qualification keeps predicate labels clear of declared prefixes: bare `tag:note` would read as prefix `tag`.

Hoplite's dialect relaxes strict `PN_LOCAL` in one way: raw `/` is allowed in local names — paths are just strings here; a strict-Turtle export escapes them (`\/`) or uses full-IRI form. The relaxation covers any character that is unambiguous mid-token — dots, dashes, slashes. Token delimiters stay out of reach: whitespace separates terms in every Turtle-shaped context, so `:topic:property graphs` is unwritable however permissive the dialect (open question 1).

### Cross-repo growth path

Corpus and vocabulary uris are relative names; url nodes are absolute. The vault segment (`<vault>/docs/foo.md` in the cross-repo model of [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]]) is the base that makes identity global: the vault plays the IRI authority, and a vault-qualified graph is the seed of an RDF named graph.

### Open questions

Held for the importer:

1. **Token-breaking characters in enumerable values.** `topic: property graphs` is categorical and wants to be a walkable value node, but whitespace ends a query-language term. Percent-encode, slugify at import, or a quoted-term form; undecided. Demoting to a literal loses the walkability that makes a categorical value worth interning.
2. **Anchors.** The wikilink grammar admits `doc#section` and `doc#^block` targets. Whether an anchored target earns its own node or resolves to the document's node is unresolved.
3. **The register presentation.** Kind dispatch landed relationally — the `document` and `url` namespace rows — so what remains of the kind-rooted register question is presentation only: whether the projection ever shows `document:`/`url:` prefixes, or the bare-canonical forms stand permanently.
4. **One label, two value kinds.** Nothing yet forbids one predicate from both interning value nodes (`summary:draft`) and holding literal rows (`summary:<doc-uri>`) — and dictionary-first resolution would let the value nodes shadow the literal projections. The likely rule is uniform routing — a predicate's objects are all value nodes or all literal rows, never both — but it is unruled; until then the shadowing case is undefined.

## namespace

The namespace dictionary: the interned roots of the address space — `document`, `url`, `predicate`, and one row per value-interned label (`tag`, `priority`, `created`). A namespace row exists exactly when stored nodes live under it; literal-valued labels own no stored nodes, so they claim no row. `name` is unique, which is what enforces the reserved words (see [Addressing](#addressing)).

## node

The node dictionary: one row per resource — the terms of every triple's subject and object positions. `id` is identity within the graph; `(nsid, uri)` is the external address, presented by projection (see [Addressing](#addressing)). A node holds identity and nothing more; a resource's facts attach through statements.

Variants derive from the namespace and the facets — the address and the rows carry the kind:

- **document** — a `document`-namespace node with [literal](#literal) rows. The witness is `content_hash`, computed for every real file: bytes exist behind the node exactly when the hash literal does.
- **ghost** — a `document`-namespace node named before its file exists; literal rows arrive when the file does.
- **url** — a `url`-namespace node: an external resource.
- **value** — a node in its label's namespace, the value as the local name. Interned at first assertion and shared by every subject that asserts it — the sharing is what makes values walkable.
- **predicate** — a `predicate`-namespace node with a [registration](#predicate) row: the vocabulary's own entries, interned at first use as a predicate — authored as a key or edge label, or computed by the importer.

Literal nodes (`summary:<doc-uri>`, `title:<doc-uri>`, `content_hash:<doc-uri>`, `minhash:<doc-uri>`) are projections: a literal address derives from subject + predicate, so the graph layer projects the node and its statement from the [literal store](#literal) on demand.

## node_alias

Alternate identities: additional uris that resolve to a node, asserted by the author — on rename, for example, so old wikilinks still reach the file. A resolution index: an alias is globally unique and maps to one node, so it is the primary key; the reverse index answers "what are node X's aliases?". An alias is a flat authored string where the canonical identity is the `(nsid, uri)` pair — which is why the alias table earns its keep as its own resolution stage.

Literal addresses inherit a document's aliases for free, since they embed its uri.

## predicate

The predicate registration: the single-column table that licenses a node for the middle position. A predicate is special by role — a statement needs a relationship in its middle position, so the edge's middle column is typed to this table alone, and the constraint is live under the importer's connection (see [Rebuild](#rebuild)). Everything else about a predicate lives in the dictionary: its uri is `predicate:<label>`, so the label needs no column here, and as a node it also stands as a subject or object — statements about the vocabulary (`cites inverse-of cited-by`, `supersedes defined-by <doc>`) are stored like any triple, never enforced.

One flat open vocabulary: the former property keys (`tag`, `status`, `created`) and the edge labels (`cites`, `supports`, `supersedes`, `links-to`) are the same kind of thing, interned at first use as a predicate — a node row plus a registration row, whether authored as a key or edge label or computed by the importer. The vocabulary is open and author-coined; surveying it is a scan of the `predicate` namespace.

The registration repeats the derivation pattern: a document is a node with literal rows; a predicate is a node with a registration row.

## edge

A statement — an RDF triple: subject, predicate, object, weighted by confidence. One row per triple; what the old model stored as one edge carrying a set of labels is several statements here. `confidence` is per-statement — the RDF-star annotation, carried in-row. An authored statement carries 1.0; an inferred one carries its inference score.

The triple is its own key: the primary key is the statement's identity, derived from the corpus and stable across rebuilds.

Two-pass build: asserted statements load first; inferred ones follow and collide out against the primary key. The author's word wins by insertion order, which is the whole provenance record.

Traversal indexes — the `WITHOUT ROWID` table is clustered on its primary key, so forward traversal (seek `src`, optionally narrowed by predicate, read `dst` and `confidence`) is covered by the table itself:

- `idx_edge_dst` — reverse traversal: seek `dst`, optionally narrowed by predicate, read `(src, confidence)`.
- `idx_edge_predicate` — predicate-led access: every statement carrying a predicate ("all cites edges", "all docs with a status"), covering `(src, dst, confidence)`.

## literal

The literal store: the long-literal half of the term dictionary, where a conventional triple store keeps the literals too large to intern. A value node carries its value in the address; a literal holds the values that outgrow one — freeform text (`title`, `summary`) and blobs (`content_hash`, `minhash`) — one row per subject per literal-valued predicate. (`created` sits on the value-node side of that line: the date rides the address, `created:2026-06-30`, and temporal ordering rides the dictionary's uri index — see [Addressing](#addressing).)

The `PRIMARY KEY (predicateid, nodeid)` mirrors the address (`<predicate-label>:<node-uri>`) and enforces the functional constraint: one value per document per literal. Predicate-first clustering groups each predicate's values contiguously, so bulk sweeps — every `minhash` for near-duplicate inference, every `summary` for the FTS feed — are single range scans, while assembling one document's facet is a few exact seeks over the known literal-valued predicates. The bare `value` column uses SQLite's per-row typing — text and blob coexist; the escape hatch, if that proves too loose, is a `datatype` column on `predicate` — declared once per predicate, matching `owl:DatatypeProperty`.

A new literal-valued predicate is data: `title`, `summary`, and any future out-of-line predicate are rows here, plus a node and its registration.

Resolution of a literal uri is specified under [Addressing](#addressing); inside the database, a literal's address is the composite key `(predicateid, nodeid)` — derived from the corpus and stable across rebuilds.

## fts

Full-text search over each document's text projection (title, summary, body), powering ranked lexical search. `uri` is stored `UNINDEXED` only to tie a hit back to its node; the porter/unicode61 tokenizer gives stemmed matching. Title and summary feed from the literal store; body comes from the file at index time.

## Survey

Survey is match and walk over the graph proper: the vocabulary is real rows in the dictionary, so surveying predicates is a scan of the `predicate` namespace and surveying a key's values is a scan of its own — ordered seeks on the `(nsid, uri)` index, which is what retired the old namespace view.
