---
title: Implementation
summary: "[Implementation, day-one] How the contracts in data-model.md and behavior.md map onto the in-memory graph plus a disposable SQLite FTS5 index."
tags: [hoplite, mcp, implementation]
created: 2026-05-25
aliases: []
---

## Overview

Hoplite is an in-memory property graph over a corpus of markdown files. The corpus of `.md` files is the only persistent state. At MCP server startup, a two-pass walker builds the graph from frontmatter and body content; everything else — edges, MinHash signatures, the FTS5 text index, the alias and casefold lookup tables — is derived and held in RAM.

SQLite returns in two roles, both transient:

- An in-memory `:memory:` database holds the FTS5 virtual table that powers `hoplite_match_nodes`. Built at startup; never written to disk.
- A persistent SQLite file gets written only on demand by `hoplite_dump_index`, for SQL-level debugging. The runtime never reads it back; it's a snapshot.

The four-tool surface is documented in [tool-api.md](tool-api.md). The behavior rules are in [behavior.md](behavior.md).

## Server module and transport

Python module: `hoplite_mcp` (following the `{service}_mcp` convention).

Transport: stdio. Day-one deployment is local, single-user, single-corpus — the Claude Code client or another MCP-aware host spawns the server as a subprocess and communicates over stdin/stdout. Per MCP convention for stdio servers, all logging goes to stderr; stdout is reserved for the JSON-RPC protocol traffic.

## Lifespan and initialization

The MCP server runs the corpus walker at startup — there's no separate `init_corpus` tool, no uninitialized mode, no first-call setup. The `lifespan=app_lifespan` async context manager walks the corpus rooted at `Path.cwd()`, builds the `Graph` instance, and stores it in server state. Tool handlers read the graph from lifespan-scoped state.

If the corpus is empty (zero `.md` files under CWD), the graph is empty too — tools still serve, they just return empty results. There's no error condition for an empty corpus.

## The Graph module

`Graph` is the in-memory container. Its shape:

```python
@dataclass
class Graph:
    documents: dict[str, Document]           # canonical path → Document
    tags: dict[str, Tag]                     # canonical slug → Tag
    out_edges: dict[str, list[Edge]]         # source ID → outgoing edges
    in_edges: dict[str, list[Edge]]          # target ID → incoming edges
    aliases: dict[str, str]                  # alternate path → canonical path
    casefold_index: dict[str, str]           # casefolded key → canonical key
    fts: sqlite3.Connection                  # in-memory :memory: with FTS5 table
```

`Document`, `Tag`, and `Edge` are frozen dataclasses; the `Graph` container is mutable. Entity field shapes are documented in [data-model.md](data-model.md).

The `casefold_index` covers both document paths and tag slugs — lookup is case-insensitive ordinal (`str.casefold()`), so `[[Notes/Foo.MD]]` and `[[notes/foo.md]]` resolve to the same canonical key.

## The walker

The walker builds the `Graph` from disk in two logical passes plus an aggregate pass.

### Pass 1: identity collection

Glob `**/*.md` under `Path.cwd()`. For each file:

1. Read only the YAML frontmatter block (the content between the opening `---` and the closing `---`).
2. Parse the mandatory fields (`title`, `summary`, `tags`, `created`, `aliases`) plus any user-defined fields.
3. If the frontmatter is missing or unparseable, or any mandatory field is missing, record a warning and skip this file. The walker doesn't synthesize defaults.
4. Create a `Document` skeleton with `resolved=true` and `body=None, content_hash=None, minhash=None` (these get populated in pass 2).
5. Register the document under its relative path; register each alias in the aliases dict; populate the casefold index for both the canonical path and each alias.

After pass 1, `Graph.documents` holds every real document and `Graph.aliases` knows how to resolve any alternate path. The lookup table is complete before any wikilink is parsed — required because pass 2's wikilink resolution depends on knowing every canonical and alias up front.

### Pass 2: body load, edges, indexes

For each `Document` registered in pass 1:

1. Read the file body (everything after the closing `---` fence).
2. Compute the sha256 content hash; store on the Document.
3. Parse `[[wikilink]]` references from the body. The parser returns a list of `(target_text, line, column)` tuples — see [wikilinks](#wikilinks) below.
4. For each wikilink target, resolve via the casefold index → alias index → canonical path. If the target resolves, emit a `mentions` edge from this document to the canonical target. If the target doesn't resolve, materialize a ghost `Document` (see [Ghost documents](#ghost-documents)) and emit the edge to it. The walker dedupes per resolved target: multiple wikilinks from one document to the same target collapse to a single edge.
5. For each tag slug in the document's frontmatter `tags` list, ensure the corresponding `Tag` entity exists in `Graph.tags` (create on first sight) and emit a `member` edge from the tag to this document.
6. Compute the MinHash signature of the body. Store on the Document.
7. Insert into the in-memory FTS5 table: `(path, title, summary, body)`.

After pass 2, every `mentions` and `member` edge is in place; FTS5 holds every body; every document has a MinHash signature.

### Aggregate pass: `related` edges

After pass 2, run pairwise MinHash similarity:

1. For every pair of resolved documents `(d1, d2)` where `d1 < d2` (path-ordered to avoid double-counting), compute Jaccard similarity from the two MinHash signatures.
2. If similarity is above the configured threshold (default 0.20), emit two `related` edges — `(d1, d2)` and `(d2, d1)` — each with `confidence` set to the similarity score.

Pairwise scan is O(N²) but cheap at our scale (128-int Jaccard comparisons are fast — ~100ms for 1000 documents). LSH bucketing is the optimization to reach for at much larger N; deferred to [roadmap.md](roadmap.md).

### Ghost documents

A wikilink whose target doesn't resolve to a real document materializes a **ghost document**:

```python
Document(
    path=target_text_after_casefold_normalization,
    resolved=False,
    title=None,
    summary=None,
    body=None,
    tags=frozenset(),
    aliases=(),
    content_hash=None,
    created=None,
    minhash=None,
)
```

The ghost is registered in `Graph.documents` like any other document. Inbound `mentions` edges point at it. On the next reindex, if a real `.md` file at the ghost's path now exists, pass 1 will create a resolved `Document` at that path — replacing the ghost in place. Inbound edges already point at the right key; no edge re-pointing needed.

## Wikilinks

Wikilink extraction lives in `wikilinks.py`. The function signature is:

```python
def extract(body: str) -> list[tuple[str, int, int]]: ...
```

Each tuple is `(target_text, line, column)`, 1-indexed. The walker discards line and column after resolution; the day-one `Edge` model carries no source-position metadata. If a future tool needs to locate a wikilink in source, re-parse the body.

Target text is whatever appeared between `[[` and `]]`, with leading and trailing whitespace stripped. The walker passes the target through case-insensitive ordinal lookup against the alias and canonical-path indexes.

## FTS5 setup

The in-memory FTS5 table is defined once at startup:

```sql
CREATE VIRTUAL TABLE fts USING fts5(
    path UNINDEXED,
    title,
    summary,
    body,
    tokenize = 'porter unicode61'
);
```

`path` is `UNINDEXED` because it's never queried as a search term — it rides along as a result column.

At query time, `hoplite_match_nodes` runs:

```sql
SELECT path, summary, bm25(fts) AS score
FROM fts
WHERE fts MATCH ?
ORDER BY score
LIMIT ?
```

The tag predicate applies as a Python-level post-filter against the in-memory `out_edges` for each candidate's tags. BM25 default parameters (`k1 = 1.2`, `b = 0.75`).

The FTS5 connection is held inside `Graph.fts` for the server's lifetime. It's never persisted; on every reindex it's torn down and rebuilt.

## MinHash

Signatures are 128 × uint64 (1024 bytes) per document. The hash family derives k independent hash functions from a base hash via universal hashing modulo Mersenne prime `M_61 = 2^61 - 1`: `h_i(x) = (a_i * base_hash(x) + b_i) mod M_61` for fixed constants `a_i, b_i`.

Configuration:

- `minhash_signature_size` (default 128)
- `minhash_shingle_size` (default 5) — word n-gram width
- `minhash_threshold` (default 0.20) — minimum Jaccard for `:related` edge materialization

Signatures live as `bytes` on the `Document` dataclass. Never persisted; recomputed at every startup. Cold-start cost is ~50ms per document, dominating walker time at 1000-doc corpora (~50s total). Acceptable for a long-running MCP server; revisit if corpora ever exceed ~5000 documents.

## Cold-start budget

At 1000 documents (~5KB average body size):

- Walk + body load: ~150ms (read ~5MB from SSD)
- FTS5 populate: ~500ms (C-backed tokenization)
- MinHash compute: ~50s (the dominant cost)
- Pairwise MinHash for `:related`: ~100ms

Total: ~50s. Scales roughly linearly; 100 docs ≈ 5s, 5000 docs ≈ 5 minutes. The cost is decision-reversible — if corpora grow past tolerable startup time, a `.hoplite/cache.db` for MinHash signatures can return without changing the rest of the architecture.

## `hoplite_dump_index` schema

The one-shot SQLite snapshot at `.hoplite/index.sqlite` (or caller-supplied path) is a normalized property-graph projection: a central `nodes` table assigns every document and tag an integer id, and `edges` connects them through foreign-key references.

```sql
CREATE TABLE nodes (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL  -- 'document' | 'tag'
);

CREATE TABLE documents (
  id INTEGER PRIMARY KEY REFERENCES nodes(id),
  path TEXT NOT NULL UNIQUE,
  resolved INTEGER NOT NULL,
  title TEXT,
  summary TEXT,
  body TEXT,
  content_hash TEXT,
  created_at REAL,
  updated_at REAL,
  minhash BLOB
);

CREATE TABLE tags (
  id INTEGER PRIMARY KEY REFERENCES nodes(id),
  slug TEXT NOT NULL UNIQUE,
  text TEXT NOT NULL,
  summary TEXT
);

CREATE TABLE document_aliases (
  document_id INTEGER NOT NULL REFERENCES documents(id),
  alias TEXT NOT NULL,
  PRIMARY KEY (document_id, alias)
);

CREATE TABLE edges (
  src INTEGER NOT NULL REFERENCES nodes(id),
  dst INTEGER NOT NULL REFERENCES nodes(id),
  kind TEXT NOT NULL,
  confidence REAL,
  PRIMARY KEY (src, dst, kind)
);
CREATE INDEX idx_edges_src ON edges(src);
CREATE INDEX idx_edges_dst ON edges(dst);

CREATE VIRTUAL TABLE fts USING fts5(path, title, summary, body);
```

Notes:

- `nodes.id` values are assigned at dump time (deterministic by sort: documents first ordered by path, then tags ordered by slug). The in-memory graph keys on strings (paths and slugs); ids exist only in the dump.
- `documents.resolved` is the ghost-vs-real flag. Ghost documents have `resolved = 0` and `title, summary, body, content_hash, created_at, updated_at, minhash` all `NULL`.
- `documents.updated_at` is populated from git history if the corpus is a git repo; `NULL` otherwise.
- `fts` is the same shape as the production in-memory mirror — lets developers reproduce match scoring with `SELECT path, bm25(fts) FROM fts WHERE fts MATCH ? ORDER BY rank`. The FTS table keys on `path`, not `nodes.id`, because that's how the runtime mirror is built.
- `edges.confidence` is nullable: `related` edges populate it with the MinHash similarity score; `member` and `mentions` edges leave it `NULL`.
- Edges are `(src, dst, kind)` unique. Multiple wikilinks from one document to the same target collapse to a single `mentions` edge.

The dump operation opens the destination, drops any prior tables (so the file is fully overwritten), runs the DDL above, bulk-inserts from the in-memory dicts, and returns a `WriteResult` with the absolute output path and per-table row counts.

## Failure modes

Almost all failure modes collapse compared to the pre-pivot SQLite-persistence design. The two persistence locations were the file and the database; with no persistent database, there's nothing to keep in sync.

### Frontmatter parse failures

A document with malformed frontmatter or missing mandatory fields is skipped from the in-memory graph and surfaced as a warning in the `hoplite_reindex` result. Fix the file's frontmatter and re-run reindex.

### Wikilinks to ghosts

Not a failure mode — wikilinks to nonexistent targets materialize ghost documents (see [Ghost documents](#ghost-documents)). The ghost set is queryable as the user's "open loops" backlog.

### Server crash

The corpus on disk is untouched; the next server start rebuilds the graph from scratch. No recovery, no repair tool, no rollback semantics.

### Dump destination unwritable

`hoplite_dump_index` validates the destination path before attempting to write. An unwritable path surfaces as a structured error response with `isError: true`.

### Out-of-date graph between writes

Day one, the in-memory graph reflects the corpus state as of the last `hoplite_reindex` call (or server startup). Files written between reindex calls don't show up until the next reindex. Agents who write files call `hoplite_reindex` explicitly. Humans editing in Obsidian see changes after the next agent-initiated reindex.

The aspirational upgrade is per-query stat-checking — see [roadmap.md](roadmap.md).

## Concurrency

Single writer, single reader, single server process. Multi-writer support is deferred ([roadmap.md](roadmap.md)). The in-memory graph isn't safe for concurrent mutation from multiple threads; the MCP server's single-threaded request handler is the lock.
