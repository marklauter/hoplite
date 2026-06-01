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
CREATE TABLE node (
  id INTEGER PRIMARY KEY,
  uri TEXT NOT NULL UNIQUE COLLATE NOCASE,
  resolved INTEGER NOT NULL,
  content_hash TEXT,
  minhash BLOB
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
CREATE TABLE property_key (
  id INTEGER PRIMARY KEY,
  key TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- Typed key/value attributes hung on a node — a resource's frontmatter and
-- metadata (tags, status, and the like). This is the data the property-graph
-- filter searches when answering "which nodes have this property?". The key is
-- interned: keyid points at property_key, so the attribute name is stored once
-- in the vocabulary and referenced by integer here.
CREATE TABLE node_property (
  nodeid INTEGER NOT NULL REFERENCES node(id),
  keyid INTEGER NOT NULL REFERENCES property_key(id),
  value TEXT NOT NULL,
  PRIMARY KEY (nodeid, keyid, value)
) WITHOUT ROWID;
-- Property-graph filter: find nodes BY property (WHERE keyid = ? [AND value = ?]).
-- The PRIMARY KEY index leads with nodeid, so it only answers "what are node X's
-- properties?"; this index leads with keyid to answer the reverse — "which nodes
-- have this property?" — the lookup behind tag/property filtering. Resolve the
-- key string to its keyid through property_key first, then seek here.
CREATE INDEX idx_node_property_key_value ON node_property(keyid, value);

-- The interned vocabulary of edge kinds — two, by provenance: declared
-- (authored) and discovered (inferred). Normalized out so each edge stores a
-- small integer kind instead of repeating the kind string on every row.
CREATE TABLE edge_kind (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- A directed relationship between two nodes — the graph's edges (declared
-- wikilinks, discovered neighborhoods). kind names the provenance; confidence
-- weights it; UNIQUE(src, dst) allows at most one edge per ordered pair of nodes.
CREATE TABLE edge (
  id INTEGER PRIMARY KEY,
  src INTEGER NOT NULL REFERENCES node(id),
  dst INTEGER NOT NULL REFERENCES node(id),
  kind INTEGER NOT NULL REFERENCES edge_kind(id),
  confidence REAL NOT NULL,
  UNIQUE (src, dst)
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
CREATE INDEX idx_edge_kind_src ON edge(kind, src, dst, confidence);
CREATE INDEX idx_edge_dst ON edge(dst, kind, src, confidence);

-- The interned vocabulary of edge stereotypes — the open-ended set of labels an
-- author applies to a declared edge (cites, supports, supersedes, contradicts,
-- not-related, ...). This is the edge-side counterpart to property_key: the
-- surveyable namespace an agent reads to learn what link-meanings the corpus
-- uses before filtering edges by one. Interning here is the same move keys get —
-- the survey-find namespace is interned on both sides; only walk-reached node
-- values stay inline. Open vocabulary, the label stored once and referenced by id.
CREATE TABLE stereotype (
  id INTEGER PRIMARY KEY,
  label TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- An edge's description: the stereotype labels it carries, classifying what kind
-- of link it is. An edge may carry several (PRIMARY KEY (edgeid, stereotypeid)
-- holds a set and dedupes within it). Unlike a node, an edge has no open
-- key/value vocabulary — its only authored description is the stereotype — so
-- this is a dedicated junction table, not an EAV property bag mirrored off
-- node_property, and the label interns through `stereotype` rather than
-- repeating on every row.
CREATE TABLE edge_stereotype (
  edgeid INTEGER NOT NULL REFERENCES edge(id),
  stereotypeid INTEGER NOT NULL REFERENCES stereotype(id),
  PRIMARY KEY (edgeid, stereotypeid)
) WITHOUT ROWID;
-- Reverse lookup: which edges carry a given stereotype (WHERE stereotypeid = ?).
-- The PRIMARY KEY leads with edgeid ("what are edge X's stereotypes?"); this
-- index leads with stereotypeid for the reverse — edges filtered by stereotype.
-- Surveying the edge vocabulary needs neither index: it is a read of `stereotype`.
CREATE INDEX idx_edge_stereotype ON edge_stereotype(stereotypeid, edgeid);

-- Full-text search over each node's text projection (title, summary, body),
-- powering ranked lexical search. uri is stored UNINDEXED only to tie a hit
-- back to its node; the porter/unicode61 tokenizer gives stemmed matching.
CREATE VIRTUAL TABLE fts USING fts5(
  uri UNINDEXED,
  title,
  summary,
  body,
  tokenize = 'porter unicode61',
  detail = 'column'
);
