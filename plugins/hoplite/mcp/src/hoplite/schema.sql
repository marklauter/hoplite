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
-- Two-pass edge build: declared edges (authored, e.g. wikilinks) are inserted
-- first and always win; discovered edges (inferred) follow and collide out
-- against UNIQUE(src, dst).
-- That precedence is enforced by the schema, not by loader comparison logic.

-- A node is the graph's vertex: one row per addressable byte resource (in
-- Hoplite, a markdown file in the corpus). uri is its medium-agnostic identity;
-- resolved marks whether the referent actually exists or is a dangling target;
-- content_hash and minhash are exact and similarity fingerprints of the bytes,
-- for change detection and near-duplicate detection.
create table node (
  id integer primary key,
  uri text not null unique collate nocase,
  resolved integer not null,
  content_hash text,
  minhash blob
);

-- The interned vocabulary of property keys — the open-ended set of frontmatter
-- attribute names the corpus uses (tags, status, created, and the like). Unlike
-- edge_kind, a closed enum of two, this grows as authors coin keys; it is open
-- vocabulary, bounded only by the count of distinct labels (dozens), never the
-- count of property rows (thousands). It earns its own table on two grounds:
--   * Interning — "tags" stops repeating its string on every node that carries
--     it; node_property stores a small integer keyid instead.
--   * Survey — this IS the property vocabulary an agent reads to learn what
--     predicates are composable, recovered as a table scan of a few dozen rows
--     rather than SELECT DISTINCT over the widest table in the graph.
-- Edge property keys will intern against this same pattern in a later pass.
create table property_key (
  id integer primary key,
  key text not null unique collate nocase
);

-- Typed key/value attributes hung on a node — a resource's frontmatter and
-- metadata (tags, status, and the like). This is the data the property-graph
-- filter searches when answering "which nodes have this property?". The key is
-- interned: keyid points at property_key, so the attribute name is stored once
-- in the vocabulary and referenced by integer here.
create table node_property (
  nodeid integer not null references node(id),
  keyid integer not null references property_key(id),
  value text not null,
  primary key (nodeid, keyid, value)
) without rowid;
-- Property-graph filter: find nodes BY property (WHERE keyid = ? [AND value = ?]).
-- The PRIMARY KEY index leads with nodeid, so it only answers "what are node X's
-- properties?"; this index leads with keyid to answer the reverse — "which nodes
-- have this property?" — the lookup behind tag/property filtering. Resolve the
-- key string to its keyid through property_key first, then seek here.
create index idx_node_property_key_value on node_property(keyid, value);

-- The interned vocabulary of edge kinds — two, by provenance: declared
-- (authored) and discovered (inferred). Normalized out so each edge stores a
-- small integer kind instead of repeating the kind string on every row.
create table edge_kind (
  id integer primary key,
  kind text not null unique collate nocase
);

-- A directed relationship between two nodes — the graph's edges (declared
-- wikilinks, discovered neighborhoods). kind names the provenance; confidence
-- weights it; UNIQUE(src, dst) allows at most one edge per ordered pair of nodes.
create table edge (
  id integer primary key,
  src integer not null references node(id),
  dst integer not null references node(id),
  kind integer not null references edge_kind(id),
  confidence real not null,
  unique (src, dst)
);
-- Edge indexes, asymmetric by design — the two directions have different
-- access patterns, so they lead with different columns:
--
--   idx_edge_kind_src — kind-leading. Serves global "all edges of kind K"
--     enumeration (e.g. every `declared` edge, unanchored) AND forward
--     kind-filtered traversal (seek kind+src), both as covering seeks.
--     Forward any-kind traversal (src alone) doesn't use this index — the
--     UNIQUE(src,dst) auto-index gives it a clean src seek, just non-covering
--     so kind/confidence cost a row lookup per edge.
--
--   idx_edge_dst — anchor-leading on dst. Serves reverse / "backtrack"
--     traversal both any-kind (seek dst) and kind-filtered (seek dst+kind) as
--     covering seeks. Reverse needs no kind-leading index of its own: global
--     by-kind enumeration is direction-agnostic, already covered above.
--
-- Trailing neighbor + confidence make each index covering for a walk. Seeking
-- by kind-alone and by dst-alone need different leading columns; that is why
-- this is two purpose-built indexes, not one symmetric pair.
create index idx_edge_kind_src on edge(kind, src, dst, confidence);
create index idx_edge_dst on edge(dst, kind, src, confidence);

-- The interned vocabulary of edge stereotypes — the open-ended set of labels an
-- author applies to a declared edge (cites, supports, supersedes, contradicts,
-- not-related, ...). This is the edge-side counterpart to property_key: the
-- surveyable namespace an agent reads to learn what link-meanings the corpus
-- uses before filtering edges by one. Interning here is the same move keys get —
-- the survey-find namespace is interned on both sides; only walk-reached node
-- values stay inline. Open vocabulary, the label stored once and referenced by id.
create table stereotype (
  id integer primary key,
  label text not null unique collate nocase
);

-- An edge's description: the stereotype labels it carries, classifying what kind
-- of link it is. An edge may carry several (PRIMARY KEY (edgeid, stereotypeid)
-- holds a set and dedupes within it). Unlike a node, an edge has no open
-- key/value vocabulary — its only authored description is the stereotype — so
-- this is a dedicated junction table, not an EAV property bag mirrored off
-- node_property, and the label interns through `stereotype` rather than
-- repeating on every row.
create table edge_stereotype (
  edgeid integer not null references edge(id),
  stereotypeid integer not null references stereotype(id),
  primary key (edgeid, stereotypeid)
) without rowid;
-- Reverse lookup: which edges carry a given stereotype (WHERE stereotypeid = ?).
-- The PRIMARY KEY leads with edgeid ("what are edge X's stereotypes?"); this
-- index leads with stereotypeid for the reverse — edges filtered by stereotype.
-- Surveying the edge vocabulary needs neither index: it is a read of `stereotype`.
create index idx_edge_stereotype on edge_stereotype(stereotypeid, edgeid);

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

-- The surveyable vocabulary as a derived view, not a base table: the union of
-- the three interning namespaces, each entry projected as a uri-style path —
-- `<source>/<value>` (stereotype/cites, property_key/tags, edge_kind/declared) —
-- so a vocabulary entry is addressable in the same segmented form as a node uri.
-- property_key and stereotype are open vocabularies (the keys and edge labels
-- authors coin); edge_kind is the closed two-value provenance enum, folded in so
-- one read returns the whole namespace. No denormalized table to keep in sync —
-- the view runs three index scans over tiny tables on demand and rides the
-- drop-and-recreate rebuild for free. order by 1 groups by source prefix, then value.
create view namespace as
select 'stereotype/' || label as namespace from stereotype
union all
select 'property_key/' || key from property_key
union all
select 'edge_kind/' || kind from edge_kind;

create view property_value as
select distinct 'property_key/' || pk.key || '/' || np.value as namespace
from node_property np
join property_key pk on pk.id = np.keyid;
  