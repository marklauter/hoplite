---
title: Schema
summary: "The SQLite schema for the Hoplite knowledge graph — nodes, the document facet, edges, the interned vocabularies, FTS, and the namespace view."
tags: [hoplite, schema, reference]
created: 2026-06-21
status: evolving
---

# Schema

The canonical SQLite schema for the Hoplite knowledge graph: a property graph over the markdown corpus plus an FTS5 lexical index, rebuilt by drop-and-recreate. This spec is the source of truth — the MCP server's `schema.sql` mirrors it, never the other way around.

```sql
-- Hoplite knowledge graph: a property graph over addressable byte resources
-- (the markdown corpus), plus an fts5 lexical index. The graph is rebuilt by
-- drop-and-recreate, never incrementally — so the dominant cost is the bulk
-- load, and the biggest performance levers live in the loader, NOT this file:
--
--   * Load the whole rebuild inside a single transaction.
--   * During the rebuild, relax durability pragmas — journal_mode and
--     synchronous — since a crash just means re-running the rebuild.
--   * foreign_keys enforcement is OFF by default in SQLite. The REFERENCES
--     clauses below are free documentation unless enforcement is enabled; if
--     it is, every insert pays a check the builder doesn't need for data it
--     constructs consistently itself. Decide deliberately whether to turn it on.
--
-- Two-pass edge build: asserted edges (e.g. wikilinks the author writes) are
-- inserted first and always win; inferred edges follow and collide out
-- against UNIQUE(src, dst). That precedence falls out of insertion order — the
-- asserted batch loads first — so no per-edge provenance need be recorded.
--
-- Every defined attribute earns a first-class home: a scalar fact is a column
-- (on node, or on the document facet for a resolved document), a label set
-- interns into its own vocabulary plus a junction (tag, predicate), and an
-- alternate identity resolves through node_alias. That leaves node_property
-- purely for open vocabulary — author-coined keys with no model-defined meaning.

-- A node is the graph's vertex: one row per addressable resource, whatever its
-- variant (document, ghost, url). id is its identity within the graph; uri is
-- its external, medium-agnostic identity; resolved marks whether it backs a real
-- resource or is a dangling target. Everything specific to a resolved document —
-- title, summary, fingerprints, created — lives in the document facet, not here.
create table node (
  id integer primary key,
  uri text not null unique collate nocase,
  resolved integer not null
);

-- The document facet: the attributes of a resolved document (a real .md file).
-- One row per resolved node, keyed 1:1 by nodeid — ghost and url nodes have no
-- row here, so the variant is the presence of this row and "byteless" is its
-- absence. title and summary are first-class authored description; content_hash
-- and minhash are byte fingerprints for change detection and near-duplicate
-- inference; created is the authored creation timestamp (null when omitted, with
-- git history as the fallback). fts indexes title/summary/body; this table is
-- their store.
create table document (
  nodeid integer primary key references node(id),
  title text,
  summary text,
  content_hash text,
  minhash blob,
  created text
);
-- Temporal index: order or range documents by creation date — the carrier for
-- temporal-proximity inference and date-sorted listings. created is ISO-8601
-- text, which sorts chronologically, so one index serves both order by and
-- between/`>` range scans.
create index idx_document_created on document(created);

-- Alternate identities: additional uris that resolve to a node, asserted by the
-- author (e.g. on rename, so old wikilinks still reach the file). A resolution
-- index, not a description — an alias is globally unique and maps to one node, so
-- it is the PRIMARY KEY; the reverse index answers "what are node X's aliases?".
-- It differs from node.uri only in that uri is the canonical identity.
create table node_alias (
  alias text primary key collate nocase,
  nodeid integer not null references node(id)
) without rowid;
create index idx_node_alias on node_alias(nodeid);

-- The interned vocabulary of open property keys — the author-coined frontmatter
-- attribute names with no model-defined meaning (status, priority, and the like).
-- Defined attributes (created, tags, aliases) have their own homes and never
-- appear here, so this vocabulary is purely open: it grows as authors coin keys,
-- bounded by the count of distinct labels (dozens) rather than property rows
-- (thousands). It earns its own table on two grounds:
--   * Interning — a key stops repeating its string on every node that carries
--     it; node_property stores a small integer keyid instead.
--   * Survey — this IS the open property vocabulary an agent reads to learn what
--     predicates are composable, recovered as a table scan of a few dozen rows
--     rather than SELECT DISTINCT over the widest table in the graph.
create table property_key (
  id integer primary key,
  key text not null unique collate nocase
);

-- Typed key/value attributes hung on a node — the open-vocabulary frontmatter an
-- author coins (status, priority, and the like). This is the data the
-- property-graph filter searches when answering "which nodes have this
-- property?". The key is interned: keyid points at property_key, so the attribute
-- name is stored once in the vocabulary and referenced by integer here.
create table node_property (
  nodeid integer not null references node(id),
  keyid integer not null references property_key(id),
  value text not null,
  primary key (nodeid, keyid, value)
) without rowid;
-- Property-graph filter: find nodes BY property (WHERE keyid = ? [AND value = ?]).
-- The PRIMARY KEY index leads with nodeid, so it only answers "what are node X's
-- properties?"; this index leads with keyid to answer the reverse — "which nodes
-- have this property?" — the lookup behind property filtering. Resolve the key
-- string to its keyid through property_key first, then seek here.
create index idx_node_property_key_value on node_property(keyid, value);

-- The interned vocabulary of tags — the open-ended set of classification labels a
-- document carries (note, journal, design, and the synthetic ghost/url the walker
-- injects). tags is the node-side counterpart to predicate: a label set, not a
-- key/value property, so its labels intern here and attach through a junction
-- rather than living in node_property. Open vocabulary, the label stored once and
-- referenced by id.
create table tag (
  id integer primary key,
  label text not null unique collate nocase
);

-- A node's classification: the tag labels it carries. A node may carry several
-- (PRIMARY KEY (nodeid, tagid) holds a set and dedupes within it). The node-side
-- mirror of edge_predicate — an interned label set via a junction.
create table node_tag (
  nodeid integer not null references node(id),
  tagid integer not null references tag(id),
  primary key (nodeid, tagid)
) without rowid;
-- Reverse lookup: which nodes carry a given tag (WHERE tagid = ?) — the lookup
-- behind the tagged predicate. The PRIMARY KEY leads with nodeid ("node X's
-- tags?"); this index leads with tagid for the reverse.
create index idx_node_tag on node_tag(tagid, nodeid);

-- A directed relationship between two nodes — the graph's edges (asserted
-- wikilinks, inferred neighborhoods). confidence weights it; UNIQUE(src, dst)
-- allows at most one edge per ordered pair of nodes. Edge provenance is
-- uniformly asserted — the author asserts a wikilink, the engine asserts an
-- inferred neighborhood — so it is not recorded.
create table edge (
  id integer primary key,
  src integer not null references node(id),
  dst integer not null references node(id),
  confidence real not null,
  unique (src, dst)
);
-- Edge indexes, asymmetric by design — forward and reverse traversal lead with
-- different columns, each trailing the neighbor and confidence so the index is
-- covering for a walk:
--
--   idx_edge_src — forward traversal: seek src, read (dst, confidence). The
--     UNIQUE(src,dst) auto-index already seeks by src but is non-covering for
--     confidence; this carries the trailing confidence to cover the walk.
--
--   idx_edge_dst — reverse / "backtrack" traversal: seek dst, read
--     (src, confidence).
create index idx_edge_src on edge(src, dst, id, confidence);
create index idx_edge_dst on edge(dst, src, id, confidence);

-- The interned vocabulary of edge predicates — the open-ended set of labels an
-- author applies to an asserted edge (cites, supports, supersedes, contradicts,
-- not-related, ...). The edge-side counterpart to tag: a label set the agent
-- surveys to learn what link-meanings the corpus uses before filtering edges by
-- one. Open vocabulary, the label stored once and referenced by id.
create table predicate (
  id integer primary key,
  label text not null unique collate nocase
);

-- An edge's description: the predicate labels it carries, classifying what kind
-- of link it is. An edge may carry several (PRIMARY KEY (edgeid, predicateid)
-- holds a set and dedupes within it). Unlike a node, an edge has no open
-- key/value vocabulary — its only authored description is the predicate — so
-- this is a junction table, the edge-side mirror of node_tag, and the label
-- interns through `predicate` rather than repeating on every row.
create table edge_predicate (
  edgeid integer not null references edge(id),
  predicateid integer not null references predicate(id),
  primary key (edgeid, predicateid)
) without rowid;
-- Reverse lookup: which edges carry a given predicate (WHERE predicateid = ?).
-- The PRIMARY KEY leads with edgeid ("what are edge X's predicates?"); this
-- index leads with predicateid for the reverse — edges filtered by predicate.
create index idx_edge_predicate on edge_predicate(predicateid, edgeid);

-- Full-text search over each node's text projection (title, summary, body),
-- powering ranked lexical search. uri is stored UNINDEXED only to tie a hit
-- back to its node; the porter/unicode61 tokenizer gives stemmed matching.
create virtual table fts using fts5(
  uri unindexed,
  title,
  summary,
  body,
  tokenize = 'porter unicode61',
  detail = 'column'
);

-- The surveyable namespaces as a derived view, not a base table: the union of the
-- interning vocabularies, each entry projected as a uri-style path rooted under
-- its owning entity (edge/predicate/cites, node/property/status, node/tag/note)
-- — so a namespace is addressable in the same segmented form as a node uri. tag,
-- property_key, and predicate are the open vocabularies whose labels and keys
-- authors coin. No denormalized table to keep in sync — the view runs a handful
-- of index scans over tiny tables on demand and rides the drop-and-recreate
-- rebuild for free. order by 1 groups by entity, then source, then value; the
-- branches are unioned in that alphabetical order, so the sort runs over an
-- already-ordered stream. Surveying one open property key's values —
-- node/property/<key>/<value>, the path extended a segment — is a parameterized
-- query, not a view: the survey tool parses the namespace and seeks WHERE
-- keyid = ? on idx_node_property_key_value.
create view namespace as
select 'edge/predicate/' || label as namespace from predicate
union all
select 'node/property/' || key from property_key
union all
select 'node/tag/' || label from tag
order by 1;
```
