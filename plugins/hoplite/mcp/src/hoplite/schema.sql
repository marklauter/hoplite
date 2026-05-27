CREATE TABLE document (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  resolved INTEGER NOT NULL,
  content_hash TEXT,
  minhash BLOB
);
CREATE INDEX idx_document_path ON document(path);

CREATE TABLE document_property (
  id INTEGER NOT NULL REFERENCES document(id),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (id, key, value)
);
CREATE INDEX idx_document_property_key_value ON document_property(key, value);

CREATE TABLE edge (
  id INTEGER PRIMARY KEY,
  src INTEGER NOT NULL REFERENCES document(id),
  dst INTEGER NOT NULL REFERENCES document(id),
  kind TEXT NOT NULL,
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
  path UNINDEXED,
  title,
  summary,
  body,
  tokenize = 'porter unicode61'
);
