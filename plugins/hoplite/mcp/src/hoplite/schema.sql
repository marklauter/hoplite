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
-- Two-pass edge build: hard edges (mentions/wikilinks) are inserted first and
-- always win; semantic edges follow and collide out against UNIQUE(src, dst).
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

-- Typed key/value attributes hung on a node — a resource's frontmatter and
-- metadata (tags, status, and the like). This is the data the property-graph
-- filter searches when answering "which nodes have this property?".
CREATE TABLE node_property (
  nodeid INTEGER NOT NULL REFERENCES node(id),
  key TEXT NOT NULL COLLATE NOCASE,
  value TEXT NOT NULL,
  PRIMARY KEY (nodeid, key, value)
) WITHOUT ROWID;
-- Property-graph filter: find nodes BY property (WHERE key = ? [AND value = ?]).
-- The PRIMARY KEY index leads with nodeid, so it only answers "what are node X's
-- properties?"; this index leads with key to answer the reverse — "which nodes
-- have this property?" — the lookup behind tag/property filtering.
CREATE INDEX idx_node_property_key_value ON node_property(key, value);

-- The interned vocabulary of relationship types (e.g. wikilink, related).
-- Normalized out so each edge stores a small integer kind instead of repeating
-- the kind string on every row.
CREATE TABLE edge_kind (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- A directed relationship between two nodes — the graph's edges (wikilinks,
-- related-neighborhoods). kind names the relationship; confidence weights it;
-- UNIQUE(src, dst) allows at most one edge per ordered pair of nodes.
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
--     enumeration (e.g. every `mentions` edge, unanchored) AND forward
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

-- Typed key/value attributes hung on an edge — the same shape as node_property,
-- but qualifying a relationship rather than a node.
CREATE TABLE edge_property (
  edgeid INTEGER NOT NULL REFERENCES edge(id),
  key TEXT NOT NULL COLLATE NOCASE,
  value TEXT NOT NULL,
  PRIMARY KEY (edgeid, key, value)
) WITHOUT ROWID;
-- Property-graph filter: find edges BY property (WHERE key = ? [AND value = ?]).
-- The PRIMARY KEY index leads with edgeid, so it only answers "what are edge X's
-- properties?"; this index leads with key to answer the reverse — "which edges
-- have this property?" — the lookup behind property filtering over edges.
CREATE INDEX idx_edge_property_key_value ON edge_property(key, value);

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
