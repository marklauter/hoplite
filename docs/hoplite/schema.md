---
title: Schema
summary: "The SQLite schema for the Hoplite knowledge graph — an RDF-shaped triple store over a self-describing resource dictionary: resources in namespace chains grounded at meta:meta, statements, the literal store backing the literal projections, and FTS."
tags: [hoplite, schema, reference]
created: 2026-06-21
status: evolving
---

# Schema

The canonical SQLite schema for the Hoplite knowledge graph: an RDF-shaped triple store over a self-describing resource dictionary, plus an FTS5 lexical index, rebuilt by drop-and-recreate. This spec is the source of truth; the importer's `schema.sql` mirrors it.

Every position of a statement holds a resource. Addresses are namespace chains grounded at `meta:meta`; edges and claims are the kinds licensed for the predicate position. The model is [[docs/notes/every-triple-position-is-a-resource.md]]; how it settled is [[docs/journal/2026-07-02-0139-the-reversal-every-triple-position-is-a-node.md]] (recorded under the old title); the term crosswalk is in [[docs/hoplite/glossary/README.md]]. The pre-reversal property-graph schema is preserved in git history.

## DDL

```sql
create table resource (
  id integer primary key,
  nsid integer not null references resource(id),
  uri text not null collate nocase,
  unique (nsid, uri)
);
create index idx_resource_uri on resource(uri);

create table resource_alias (
  alias text primary key collate nocase,
  resourceid integer not null references resource(id)
) without rowid;
create index idx_resource_alias on resource_alias(resourceid);

create table statement (
  src integer not null references resource(id),
  predicateid integer not null references resource(id),
  dst integer not null references resource(id),
  confidence real not null,
  primary key (src, predicateid, dst)
) without rowid;
create index idx_statement_dst on statement(dst, predicateid, src, confidence);
create index idx_statement_predicate on statement(predicateid, src, dst, confidence);

create table literal (
  predicateid integer not null references resource(id),
  resourceid integer not null references resource(id),
  value,
  primary key (predicateid, resourceid)
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
- **Every term is a resource.** Every term in every position is a row in the dictionary, addressed by its namespace chain. The predicate position is filled by an edge or claim, so statements about the vocabulary are representable — stored, never enforced. Every uri derives from the corpus, so every resource is named (RDF: no blank nodes).
- **Values are resources.** RDF permits a value to be a resource, and its practice recommends it — "things, not strings." Hoplite makes it the rule: a value interns as a resource (`priority:high`), and where an RDF literal may only end a statement, a value can begin one as well — described and walked like anything else. Bytes too large for an address live in the [literal](#literal) table behind a projection (`summary:<doc-uri>`).
- **`confidence` is the RDF-star annotation.** A statement about the statement — `<< src p dst >> hoplite:confidence n` — carried in-row: the triple's natural key makes every statement natively reified.
- **A statement is addressed by its terms.** A triple is identified by its three positions, in RDF and here alike (see [Addressing](#addressing)).
- **Names are relative references.** Corpus and vocabulary names are relative — url resources are already absolute — and RDF resolves relative references against a base. Assigning one (the vault, in the cross-repo model) makes identity global (see [Addressing](#addressing)).

## Rebuild

The graph is rebuilt by drop-and-recreate — the dominant cost is the bulk load, and the biggest performance levers live in the loader:

- Load the whole rebuild inside a single transaction.
- During the rebuild, relax the durability pragmas — `journal_mode` and `synchronous` — since a crash just means re-running the rebuild.
- `foreign_keys` enforcement is per-connection in SQLite; the importer turns it on, so the `REFERENCES` clauses are live constraints.

A rebuild is deterministic: every chain, resource, statement, and literal key derives from the corpus alone, so rebuilding reproduces the graph byte-identically.

Two invariants live in the importer rather than the DDL, which cannot express them: only members of `edge` and `claim` fill the predicate position (predicate-licensing is namespace-derived), and the namespace tree stays a tree grounded at `meta:meta`.

## Addressing

An address is a **namespace chain**: colon-joined names walking down from the root — `meta:claim:priority:high` names the value `high` under the key `priority` under `claim` under `meta`. Short forms abbreviate: any unique suffix resolves — `priority:high`, even bare `high` — the same shortest-unique discipline the wikilink grammar gives slugs. An ambiguous short form demands qualification; the importer warns when a newly coined name makes existing short forms ambiguous.

Addresses are bare strings — a scheme would be tool-api packaging, kept out of the model. The MCP tool layer is the resolver, taking an address as a parameter. Matching is case-insensitive (`collate nocase` throughout).

Authoring and addressing are separate registers. Authors write bare wikilink targets (`[[docs/tag.md]]`), per the grammar in [[docs/hoplite/expressing-edges.md]]; document-namespace resources present bare the same way. The register split is a standing rule, first drawn (in an older slash-rooted form) in [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]].

### Separators

Two separators split two naming authorities: **slash** joins path segments inside a document uri — the filesystem's namespace — and **colon** joins the links of a chain — the vocabulary's. The wikilink grammar keeps colons out of targets, so a path can never collide with a colon-bearing chain (bare single-name short forms share the path space — see [resolution](#address-kinds-and-resolution)). Colon addresses belong to the query layer; the form is Turtle's `prefix:localname` and the urn separator. The decision and its rejected alternatives are recorded in [[docs/notes/colon-separates-vocabulary-addresses-from-paths.md]].

### Address kinds and resolution

A fully qualified chain resolves from the fixed point down, and **the leaf is greedy**: at each namespace, the resolver first seeks the entire remainder as one uri — `unique (nsid, uri)` — and splits at the first colon only on a miss. Leaves keep their own colons: `created:2026-06-30T21:34` resolves whole under `created`, and `url:https://example.com:8080/x` whole under `url` — descent happens only through names that are namespaces, which values and urls never are.

A short form resolves on `idx_resource_uri` with the same greedy discipline: try the whole address as the leaf name, then move the split rightward from the first colon — seeking each candidate leaf and verifying the given links upward — and a unique survivor wins; ties demand qualification. A colon-free address runs three stages: the document namespace, then `resource_alias` (an alias is a flat authored string, colon-free by the wikilink grammar), then the same short-form seek — bare `high` resolves when unique. One caveat comes with the bare register: single names share the string space with document targets, and the document register wins — an authored `[[high]]` mints the ghost `document:high` and shadows the bare form of `priority:high`, which then needs one link of qualification.

The stored kinds:

- **document** — `document:docs/notes/foo.md`, presented bare: a corpus path.
- **ghost** — `document:tag`: identical in form to a document — the kind is the missing literal rows, not the address.
- **url** — `url:https://...`: an external reference, absolute already.
- **edge** — `edge:cites`: a pure relation, licensed for the predicate position.
- **claim** — `claim:priority`: a key, licensed for the predicate position; a value-routed key parents its values.
- **value** — `priority:high`, `tag:note`, `created:2026-06-30`: the value under its key. The `(nsid, uri)` index doubles as a per-key range index (`created:2026-06` is an ordered scan; ISO-8601 sorts lexicographically).

One kind is projected on demand:

- **literal** — `summary:<doc-uri>`: a literal-routed key parents no stored resources, so the chain's last seek misses and the resolver projects instead — key → its `claim` resource, tail → `resourceid` (aliases apply, so literal addresses survive renames), `(predicateid, resourceid)` → the value in the [literal store](#literal).

And one is addressed without a name:

- **statements** — a triple is addressed by its three terms, consistent with RDF; its one annotation, `confidence`, rides in-row.

### In the query language

Turtle-shaped contexts — the query language — qualify every address: the leading colon at minimum (`:priority:high`). Turtle's first colon is the namespace boundary (a prefix cannot contain a colon), so everything after it is the local name, where Turtle admits raw colons — a whole chain serializes as one token, unescaped. Qualification keeps chain names clear of declared prefixes: bare `priority:high` would read as prefix `priority`.

Hoplite's dialect relaxes strict `PN_LOCAL` in one way: raw `/` is allowed in local names — paths are just strings here; a strict-Turtle export escapes them (`\/`) or uses full-IRI form. The relaxation covers any character that is unambiguous mid-token — dots, dashes, slashes. Token delimiters stay out of reach: whitespace separates terms in every Turtle-shaped context, so `:topic:property graphs` is unwritable however permissive the dialect (open question 1).

A query is a triple pattern that binds positions by chain address — `subject`, `predicate`, and `object` name the positions, not namespaces — and the unbound positions are the result: `(:predicate:status :object:todo)` returns every subject whose `status` is `todo`. The position names occupy the short-form token space, so a key coined `subject`, `predicate`, or `object` would make bindings ambiguous: the pattern grammar either reserves the three names in query context or must mark positions distinctly — held with the sketch, [[docs/notes/query-patterns-bind-positions-by-chain-address.md]].

### Cross-repo growth path

Corpus and vocabulary names are relative; url resources are absolute. The vault segment (`<vault>/docs/foo.md` in the cross-repo model of [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]]) is the base that makes identity global: the vault plays the IRI authority, and a vault-qualified graph is the seed of an RDF named graph.

### Open questions

Held for the importer:

1. **Token-breaking characters in enumerable values.** `topic: property graphs` is categorical and wants to be a walkable value, but whitespace ends a query-language term. Percent-encode, slugify at import, or a quoted-term form; undecided. Demoting to a literal loses the walkability that makes a categorical value worth interning.
2. **Anchors.** The wikilink grammar admits `doc#section` and `doc#^block` targets. Whether an anchored target earns its own resource or resolves to the document's is unresolved.
3. **Canonical presentation.** Tool output could present full chains, shortest-unique forms, or the bare register per kind; undecided beyond "documents present bare."
4. **One key, two routings.** Nothing yet forbids a key from both interning values (`summary:draft`) and holding literal rows (`summary:<doc-uri>`); stored values would shadow the literal projections. The likely rule is uniform routing — a key's objects are all values or all literal rows — but it is unruled; until then the shadowing case is undefined.

## resource

The resource dictionary: one row per resource — every term of every statement. `id` is identity within the graph; `(nsid, uri)` is the address, presented by projection as the chain (see [Addressing](#addressing)). A row holds identity and nothing more; a resource's facts attach through statements.

The dictionary is self-describing: `nsid` references `resource`, so namespaces are resources, and a resource is a namespace exactly when resources live under it. The recursion grounds at one fixed point — `meta:meta`, whose `nsid` is its own id — and `meta` parents the four structural namespaces: `edge`, `claim`, `document`, `url`. Keys parent their values; there is no namespace table and no name stored twice. Projection walks up and stops at the self-parented row, emitting its name once: a canonical chain carries a single leading `meta` (`meta:claim:priority:high`), while `meta:meta` names the fixed point and resolves, as does any stack of leading `meta`s.

Kinds derive from namespace membership and the literal store — the chain and the rows carry the kind:

- **document** — a `document`-namespace resource with [literal](#literal) rows. The witness is `content_hash`, computed for every real file: bytes exist behind the resource exactly when the hash literal does.
- **ghost** — a `document`-namespace resource named before its file exists.
- **url** — a `url`-namespace resource: an external reference.
- **edge** — an `edge`-namespace resource: a pure relation.
- **claim** — a `claim`-namespace resource: a key. Value-routed keys parent their values; literal-routed keys parent projections.
- **value** — a resource under its key, the value as its uri. Interned at first assertion and shared by every subject that asserts it — the sharing is what makes values walkable.

Literal projections (`summary:<doc-uri>`, `title:<doc-uri>`, `content_hash:<doc-uri>`, `minhash:<doc-uri>`) are not stored: a literal address derives from key + subject, so the graph layer projects the resource and its statement from the [literal store](#literal) on demand.

## resource_alias

Alternate identities: additional names that resolve to a resource, asserted by the author — on rename, for example, so old wikilinks still reach the file. A resolution index: an alias is globally unique and maps to one resource, so it is the primary key; the reverse index answers "what are resource X's aliases?". An alias is a flat authored string where the canonical identity is the `(nsid, uri)` pair — which is why the alias table earns its keep as its own resolution stage.

Literal addresses inherit a document's aliases for free, since they embed its uri.

## statement

A statement — an RDF triple: subject, predicate, object, weighted by confidence. One row per triple; what the old model stored as one edge carrying a set of labels is several statements here. `confidence` is per-statement — the RDF-star annotation, carried in-row. An authored statement carries 1.0; an inferred one carries its inference score.

`predicateid` holds an edge or claim — predicate-licensing is namespace-derived, maintained by the importer (see [Rebuild](#rebuild)); `src` and `dst` hold any resource.

The triple is its own key: the primary key is the statement's identity, derived from the corpus and stable across rebuilds.

Two-pass build: asserted statements load first; inferred ones follow and collide out against the primary key. The author's word wins by insertion order — the only record of who said what.

Traversal indexes — the `WITHOUT ROWID` table is clustered on its primary key, so forward traversal (seek `src`, optionally narrowed by predicate, read `dst` and `confidence`) is covered by the table itself:

- `idx_statement_dst` — reverse traversal: seek `dst`, optionally narrowed by predicate, read `(src, confidence)`.
- `idx_statement_predicate` — predicate-led access: every statement carrying a predicate ("all cites statements", "all docs with a status"), covering `(src, dst, confidence)`.

## literal

The literal store: the long-literal half of the term dictionary, where a conventional triple store keeps the literals too large to intern. A value carries itself in its address; a literal holds the values that outgrow one — freeform text (`title`, `summary`) and blobs (`content_hash`, `minhash`) — one row per subject per literal-routed key. (`created` sits on the value side of that line: the date rides the address, `created:2026-06-30`, and temporal ordering rides the dictionary's `(nsid, uri)` index — see [Addressing](#addressing).)

The `PRIMARY KEY (predicateid, resourceid)` mirrors the address (`<key>:<doc-uri>`) and enforces the functional constraint: one value per document per key. Predicate-first clustering groups each key's values contiguously, so bulk sweeps — every `minhash` for near-duplicate inference, every `summary` for the FTS feed — are single range scans, while assembling one document's facet is a few exact seeks over the known literal-routed keys. The bare `value` column uses SQLite's per-row typing — text and blob coexist; the escape hatch, if that proves too loose, is a per-key datatype fact.

A new literal-routed key is data: `title`, `summary`, and any future out-of-line key are rows here, plus the key's resource under `claim`.

Resolution of a literal address is specified under [Addressing](#addressing); inside the database, a literal's address is the composite key `(predicateid, resourceid)` — derived from the corpus and stable across rebuilds.

## fts

Full-text search over each document's text projection (title, summary, body), powering ranked lexical search. `uri` is stored `UNINDEXED` only to tie a hit back to its resource; the porter/unicode61 tokenizer gives stemmed matching. Title and summary feed from the literal store; body comes from the file at index time.

## Survey

Survey is match and walk over the graph proper: the vocabulary is real rows in the dictionary, so surveying keys and relations is a scan under `claim` and `edge`, and surveying a key's values is a scan under the key — ordered seeks on the `(nsid, uri)` index, real interned rows where the old schema computed a view.
