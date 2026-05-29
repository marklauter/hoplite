CREATE TABLE node (
  id INTEGER PRIMARY KEY,
  uri TEXT NOT NULL UNIQUE,
  resolved INTEGER NOT NULL,
  content_hash TEXT,
  minhash BLOB
);
CREATE INDEX idx_node_uri ON node(uri);

CREATE TABLE node_property (
  id INTEGER NOT NULL REFERENCES node(id),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (id, key, value)
);
CREATE INDEX idx_node_property_key_value ON node_property(key, value);

CREATE TABLE edge_kind (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL UNIQUE
);

CREATE TABLE edge (
  id INTEGER PRIMARY KEY,
  src INTEGER NOT NULL REFERENCES node(id),
  dst INTEGER NOT NULL REFERENCES node(id),
  kind INTEGER NOT NULL REFERENCES edge_kind(id),
  confidence REAL NOT NULL,
  UNIQUE (src, dst)
);
CREATE INDEX idx_edge_kind_src ON edge(kind, src, dst, confidence);
CREATE INDEX idx_edge_kind_dst ON edge(kind, dst, src, confidence);

CREATE TABLE edge_property (
  id INTEGER NOT NULL REFERENCES edge(id),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (id, key, value)
);
CREATE INDEX idx_edge_property_key_value ON edge_property(key, value);

CREATE VIRTUAL TABLE fts USING fts5(
  uri UNINDEXED,
  title,
  summary,
  body,
  tokenize = 'porter unicode61'
);
