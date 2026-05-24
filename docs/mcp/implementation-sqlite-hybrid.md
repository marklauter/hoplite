# SQLite-hybrid implementation

[Implementation, day-one] How the contracts map onto SQLite for the relational layer with files for the prose layer.

## Overview

Notes, label envelope prose, the read envelope, and embedding blobs stay as files. Everything relational — node metadata, label metadata, label memberships, edges — lives in a single SQLite database. Search uses SQLite's FTS5 virtual table; no per-call BM25 recomputation.

The tool API surface (see [tool-api.md](tool-api.md)) and behavior contracts (see [behavior.md](behavior.md)) are implementation-agnostic and hold unchanged regardless of how the persistence layer is realized. This document describes the persistence layer.

## Server module and transport

Python module: `hoplite_mcp` (following the `{service}_mcp` convention).

Transport: stdio. Day-one deployment is local, single-user, single-corpus — the Claude Code client or another MCP-aware host spawns the server as a subprocess and communicates over stdin/stdout. No network configuration, no auth layer needed. Per MCP convention for stdio servers, all logging goes to stderr; stdout is reserved for the JSON-RPC protocol traffic.

## Lifespan and connection management

The MCP server holds a single SQLite connection for the process lifetime once the corpus is initialized. The PRAGMAs (`journal_mode = WAL`, `synchronous = NORMAL`, `foreign_keys = ON`, `busy_timeout = 5000`) apply once at connection open; FTS5 keeps internal state across queries that benefits from the persistent connection.

In Python's MCP server framework, this maps to the `lifespan=app_lifespan` pattern — an async context manager. On startup, if `<cwd>/.hoplite/graph.db` exists, the lifespan opens the connection and stores it in server state. If `.hoplite/` is absent, the lifespan stores a sentinel "uninitialized" state instead; the connection opens later when `hoplite_init_corpus` runs and is then promoted into the same lifespan-held slot. Tool handlers read the connection from lifespan-scoped state; the slot is `None` in uninitialized mode, and the dispatcher fast-paths to the "corpus not initialized" error for every tool except `hoplite_init_corpus`.

## Storage layout

Content lives anywhere under `<repo-root>/docs/`. The index lives at `<repo-root>/.hoplite/`. Two directories at the repo root, with disjoint responsibilities.

```
<repo-root>/
  docs/                                         CONTENT — all notes live here
    <slug>.<ext>                                root-level note (id: <slug>.<ext>)
    notes/<slug>.<ext>                          notes organized under notes/ (id: notes/<slug>.<ext>)
    journal/<iso-date>-<slug>.<ext>             journal entry (id: journal/...)
    mcp/<slug>.<ext>                            mcp spec page (id: mcp/...)
    ... any other folder structure the user wants
  .hoplite/                                       INDEX — opaque to authors; managed by the MCP server
    graph.db                                    SQLite database (all relational data)
    labels/<label>.md                           label envelope (pure markdown, optional prose)
    envelopes/read.md                           fixed content envelope applied by read()
    embeddings/<flat-id>.npy                    embedding blob (when reindex lands; flat-id encodes path)
```

File responsibilities:

- `docs/` contains every node's body. Subfolders organize by topic at the user's discretion; the indexer reads them as ids.
- `.hoplite/graph.db` carries every structured query target: nodes (metadata), labels (metadata), label memberships, edges, and the full-text search index.
- `.hoplite/labels/<label>.md` files carry label envelope prose.
- `.hoplite/envelopes/read.md` is the fixed content envelope.
- `.hoplite/embeddings/<flat-id>.npy` carries binary embedding vectors. The flat-id replaces `/` in the path with `-` (or another safe separator) so embedding files live flat at one level — easier for ML tooling than nested directories.

The `.hoplite/` directory is hidden (leading dot) the same way `.git/` is — mostly tool-managed metadata; humans rarely look in it. Add `.hoplite/graph.db`, `.hoplite/graph.db-wal`, and `.hoplite/graph.db-shm` to `.gitignore` (the database is regenerable from `docs/` content). The label envelope prose and read envelope are authored content the user may choose to commit alongside `docs/`.

## Database schema

```sql
CREATE TABLE nodes (
  id                  TEXT PRIMARY KEY,
  summary             TEXT NOT NULL,
  minhash_signature   BLOB,            -- MinHash signature for relatedness scoring
  embedding_path      TEXT             -- path to .npy when embeddings land
);

CREATE TABLE labels (
  id              TEXT PRIMARY KEY,
  summary         TEXT,
  has_envelope    INTEGER NOT NULL DEFAULT 0  -- 1 if .hoplite/labels/<id>.md exists
);

CREATE TABLE label_membership (
  label           TEXT NOT NULL,
  member_id       TEXT NOT NULL,
  PRIMARY KEY (label, member_id),
  FOREIGN KEY (label)     REFERENCES labels(id),
  FOREIGN KEY (member_id) REFERENCES nodes(id)
);
CREATE INDEX idx_membership_member ON label_membership(member_id);

CREATE TABLE edges (
  source_id       TEXT NOT NULL,
  type            TEXT NOT NULL,
  target_id       TEXT NOT NULL,
  confidence      REAL,
  source          TEXT,
  rationale       TEXT,
  PRIMARY KEY (source_id, type, target_id),
  FOREIGN KEY (source_id) REFERENCES nodes(id)
);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_edges_type   ON edges(type);

CREATE VIRTUAL TABLE nodes_fts USING fts5(
  id UNINDEXED,
  body,
  summary,
  tokenize = 'porter unicode61'
);
```

### PRAGMAs

The MCP server applies these PRAGMAs immediately after opening the connection at startup:

```sql
PRAGMA journal_mode = WAL;        -- write-ahead logging
PRAGMA synchronous = NORMAL;      -- standard companion to WAL
PRAGMA foreign_keys = ON;         -- enforce FK constraints
PRAGMA busy_timeout = 5000;       -- 5s wait before SQLITE_BUSY
```

`journal_mode = WAL` is load-bearing — it's what enables one writer plus many concurrent readers without blocking. The other PRAGMAs are the standard companions for a WAL-mode database.

`synchronous = NORMAL` flushes WAL pages at every commit but doesn't fsync the database file on every commit. Combined with WAL's checkpoint semantics, this is durable across application crashes and gives much better write throughput than `synchronous = FULL`. It loses durability only on OS-level crashes or power loss within a small window; acceptable for a personal-and-agentic knowledge graph.

`foreign_keys = ON` is required for FK constraints to be enforced — SQLite leaves them off by default for legacy reasons.

`busy_timeout = 5000` sets how long a write waits for the SQLite lock before erroring. With single-writer day one this rarely matters; with multi-writer it gives short-lived contention time to resolve before surfacing as an error.

WAL creates two side files alongside `graph.db`: `graph.db-wal` (the write-ahead log) and `graph.db-shm` (shared memory index). Both belong in `.gitignore` alongside `graph.db` itself. They're recreated automatically when the database is opened.

Checkpointing happens automatically; manual `PRAGMA wal_checkpoint(TRUNCATE)` can be invoked by a maintenance script if WAL file size growth becomes a concern.

## Entity-to-storage mapping

How each entity from [data-model.md](data-model.md) is realized.

### Node

Two locations per node:

- Authored content at `<corpus_root>/docs/<id>`. The id is a path expression including the file extension (`foo.md`, `notes/skill-composition.md`, `journal/2026-05-24-foo.md`, `mcp/data-model.md`). Pure markdown body, no YAML frontmatter. Body shape on lines 1-4 is fixed: `# Title` on line 1, blank on line 2, summary on line 3, blank on line 4, body sections from line 5 onward.
- Metadata: one row in `nodes` (`id`, `summary`, `minhash_signature`, `embedding_path`) plus rows in `edges` for each outbound edge. The body text is indexed in `nodes_fts` for `hoplite_match_nodes`. The signature is computed at write time and used to materialize `:related` edges; see [MinHash details](#minhash-details).

The two stores hold disjoint primary concerns: the file is the source of truth for body content; the database is the source of truth for metadata, edges, and the search index.

### Label

Up to two locations per label:

- One row in `labels` (`id`, optional `summary`, `has_envelope` boolean).
- Optional `<corpus_root>/.hoplite/labels/<label>.md` carrying envelope prose. The `has_envelope` column tracks whether the file exists; the file is authoritative.
- Rows in `label_membership` for each member.

Membership IS a relational table. Adding a node to a label is one `INSERT OR IGNORE`. Removing is one `DELETE`. Listing members is one query.

### Edge

Each edge is a row in `edges`. Symmetric `:related` edges are written as two rows (one in each direction), or queried bidirectionally via the `idx_edges_target` index — the implementation can choose either approach; the symmetry is now a query property, not a denormalization concern.

### Envelope

The framing component for `hoplite_invoke_node` comes from `<corpus_root>/.hoplite/labels/<label>.md` (the label envelope file). For `hoplite_read_node`, from `<corpus_root>/.hoplite/envelopes/read.md`. The structured `Envelope` shape is composed by the server at retrieval time; on disk it's just the envelope file plus the structure built in memory.

## Id and path rules

A node's id is the path from `docs/` including the file extension. Each path segment is lowercase kebab-case (`[a-z0-9-]`); segments are separated by `/`. Examples: `foo.md`, `notes/skill-composition.md`, `journal/2026-05-24-today-was-warm.md`, `mcp/data-model.md`.

Wiki-links use the same id form: `[[journal/2026-05-24-foo.md]]`, `[[mcp/data-model.md]]`.

The id maps directly to the authored file path: `<corpus_root>/docs/<id>`. No translation needed.

Auto-derived labels from the id:

- First path segment when present. `journal/2026-05-24-foo.md` carries `journal`; `notes/foo.md` carries `notes`; `mcp/data-model.md` carries `mcp`. Root-level ids (no folder) get no auto-derived path label.
- ISO date label when the filename component matches `<iso-date>-<slug>.<ext>`. Independent of folder; works for any note whose filename starts with a date.

## Corpus root and initialization

The corpus root IS the current working directory. The MCP server reads CWD at startup; that directory holds `docs/` (content) and `.hoplite/` (index). Hoplite installs once as a user-scope plugin; CWD differs per project, so the same server binary attaches to whichever corpus the launching host (Claude Code CLI, IDE extension, desktop app) opens.

All paths derive from CWD:

- Content: `<cwd>/docs/<id>` for every node.
- Database: `<cwd>/.hoplite/graph.db`.
- Label envelopes: `<cwd>/.hoplite/labels/<label>.md`.
- Read envelope: `<cwd>/.hoplite/envelopes/read.md`.
- Embedding blobs: `<cwd>/.hoplite/embeddings/<flat-id>.npy`.

### Uninitialized state

If `<cwd>/.hoplite/` is absent, the corpus is uninitialized. The server boots in uninitialized mode: it skips opening the database connection (there's no file to open) and rejects every tool call EXCEPT `hoplite_init_corpus` with a structured error pointing the caller at the init tool.

`hoplite_init_corpus` (see [tool-api.md](tool-api.md#hoplite_init_corpus)):

1. Create `<cwd>/.hoplite/`, `<cwd>/.hoplite/labels/`, `<cwd>/.hoplite/envelopes/`, `<cwd>/.hoplite/embeddings/`.
2. Create `<cwd>/docs/` if absent.
3. Open `<cwd>/.hoplite/graph.db`, apply PRAGMAs, run the schema DDL from [Database schema](#database-schema).
4. Write the four shipped envelope files (bundled with the plugin) into `<cwd>/.hoplite/labels/` and `<cwd>/.hoplite/envelopes/` — see [Bootstrap](#bootstrap--shipped-envelope-files). Existing files are left alone (idempotent).
5. Insert the three `labels` rows for `instruction`, `reference`, `observation` with `has_envelope = 1`.
6. Transition the server from uninitialized to initialized mode in-process — the connection from step 3 becomes the lifespan-held connection, every other tool starts working immediately.
7. Return `WriteResult` listing the corpus root path and the files created.

Idempotent across calls: a second `hoplite_init_corpus` against an already-initialized corpus is a no-op (or restores any individually missing bootstrap files). The tool only creates absent artifacts; it never overwrites authored content. Full reset to defaults is a future `repair` concern.

## Why this shape

SQLite handles every relational concern the filesystem was emulating:

- Per-label membership becomes a real indexed join table. "All nodes labeled X" is a single SELECT, fast at any corpus size.
- Bidirectional indexes — `idx_membership_member` and `idx_edges_target` let both "what labels does this node carry" and "what edges point at this node" run as indexed queries.
- Edges become a first-class table. Symmetric `:related` edges, traversal predicates, and confidence filtering all map to standard SQL.
- ACID transactions across the whole graph state. A single `hoplite_insert_node` or `hoplite_update_node` commits all node, edge, and membership changes atomically. No cross-file atomicity story to engineer.
- FTS5 gives BM25 search natively. No per-call rescoring; the index is incremental.

Prose stays in files:

- Notes are greppable, git-diffable, and hand-editable.
- Label envelope prose and the read envelope are content the agent (and the user) authors directly; their natural medium is markdown files.
- Embedding blobs are binary; SQLite BLOBs work but `.npy` files are more interoperable with ML tooling.

## Write-time flow — common steps

`hoplite_insert_node`, `hoplite_update_node`, and `hoplite_index_node` share most of the indexing flow. They differ on the existence check (step 0) and whether step 4 writes the body file. The remaining steps are shared.

Common steps, in order:

1. Validate labels. Per [behavior.md](behavior.md#slug-and-id-rules).
2. Validate the id format. Each path segment matches `[a-z0-9-]`; the id ends with `.<ext>`.
3. Validate `out_edges`. Reject any author-supplied edge that carries a `source` field.
4. Resolve the file path: `<corpus_root>/docs/<id>`.
5. Read or write the body (varies by tool — see per-tool sections).
6. Parse `[[wiki-links]]` from the body; build the `:mentions` edges.
7. Compose auto-derived labels: the first path segment of the id when present, plus the ISO date label if the filename component matches `<iso-date>-<slug>.<ext>`.
8. Parse the cached summary from the body — line 3.
9. Compute the MinHash signature of the body (tokenize on word boundaries, shingle into word n-grams, hash each shingle, keep the `k` minimum hashes). See [MinHash details](#minhash-details).
10. Materialize derived `:related` edges. Read every other node's `minhash_signature` from `nodes` (single SQL scan). Compute Jaccard similarity against this node. For each other node where similarity ≥ `minhash_threshold` (0.20 default), emit a `:related` edge with `confidence = similarity` and `source = "minhash"`. The edge is symmetric — both endpoints carry it.
11. Reconcile the outbound edge set for this node: parsed `:mentions` + author-supplied `out_edges` + freshly-derived `:related` from step 10. Dedupe by `(type, to)`.
12. Open a SQLite transaction:
    - `INSERT OR REPLACE` into `nodes` with id, summary, minhash_signature, embedding_path.
    - `DELETE FROM edges WHERE source_id = ?` then `INSERT` the reconciled edge set from step 11.
    - For each derived `:related` edge `(this, other, sim)`: `INSERT OR REPLACE INTO edges` the symmetric row `(other, this, related, sim, "minhash")`. Drop any prior row `(other, this, related, *, "minhash")` whose pair fell below threshold this pass.
    - `DELETE FROM label_membership WHERE member_id = ?` (no-op on first insert).
    - For each label the node carries: `INSERT OR IGNORE INTO labels (id, has_envelope) VALUES (?, COALESCE((SELECT has_envelope FROM labels WHERE id=?), 0))` then `INSERT INTO label_membership (label, member_id) VALUES (?, ?)`.
    - Refresh the FTS index: `DELETE FROM nodes_fts WHERE id = ?` then `INSERT INTO nodes_fts (id, body, summary) VALUES (?, ?, ?)`.
    - Commit.
13. Return `WriteResult` with id and any warnings.

The SQLite transaction in step 12 is atomic — every relational change for this write succeeds or none do, including the bidirectional `:related` edge updates.

### MinHash details

The signature lives directly on the `nodes` table as a `BLOB` column (`minhash_signature`). The signature is small (k 32-bit hashes, default k=128 → ~512 bytes) and rarely needed by read paths, so on-row storage avoids a second table while keeping the `nodes` row cache-friendly.

Configuration:

- `minhash_signature_size` (default 128) — number of hash values per signature. Larger is more accurate, slower to compare.
- `minhash_shingle_size` (default 5) — width of the word n-gram. Smaller catches shorter overlaps, more noise.
- `minhash_threshold` (default 0.20) — minimum Jaccard similarity to materialize a `:related` edge.

The step-10 pairwise scan is O(N) where N is the corpus size. For a personal corpus (hundreds to low thousands of nodes), this is sub-second per write. At very large N (10⁵+), an LSH bucketing pre-filter narrows the comparison set; deferred to [roadmap.md](roadmap.md).

Write latency takes the cost of the pairwise scan and signature recompute; reads stay on the hot path (`hoplite_match_nodes` and `hoplite_traverse_nodes` never load the signature blob unless an operator explicitly queries it).

## Insert flow

`hoplite_insert_node(id, body, labels, out_edges)`:

- Step 0 (existence check): reject if a row exists in `nodes` for the id, or if the file at the resolved path already exists.
- Step 5: write the body to the resolved path via temp-and-rename. File write is atomic per-file; cross-boundary failure modes are covered in [Atomicity](#atomicity).
- Otherwise runs the common steps.

## Update flow

`hoplite_update_node(id, body, labels, out_edges)`:

- Step 0 (existence check): reject if no row exists in `nodes` for the id, or if the file at the resolved path does not exist.
- Step 5: rewrite the body at the resolved path via temp-and-rename.
- Otherwise runs the common steps. Edge reconciliation preserves derived edges from the prior state.

## Index flow

`hoplite_index_node(id, labels, out_edges)`:

- Step 0 (existence check): reject if the file at the resolved path does not exist. The database may or may not have a prior row — `hoplite_index_node` is idempotent across both cases.
- Step 5: read the body from the resolved path. Do not write — `hoplite_index_node` indexes content that's already on disk.
- Otherwise runs the common steps. Edge reconciliation preserves derived edges if a prior database row exists.

Use cases: ingesting files created out-of-band (external editor, script, migration); re-indexing after a hand-edit changes the body; bulk-ingesting an existing folder by walking it and calling `hoplite_index_node` per file.

## Delete flow

`hoplite_delete_node(id)`:

1. Existence check. Reject if no row in `nodes` for the id.
2. Resolve the file path and unlink the file.
3. Open a SQLite transaction:
   - `DELETE FROM edges WHERE source_id = ? OR target_id = ?` (drops outgoing edges; also drops back-references in derived edges pointing at this id, since the row is going away — including the symmetric `:related` edges other nodes carried back to this one).
   - `DELETE FROM label_membership WHERE member_id = ?`.
   - `DELETE FROM nodes_fts WHERE id = ?`.
   - `DELETE FROM nodes WHERE id = ?` (drops the row and its `minhash_signature`).
   - Commit.

Wiki-link references in other notes' bodies still exist as raw `[[...]]` text but resolve to nothing — the broken-link semantic still applies. The next `hoplite_update_node`/`hoplite_index_node` to a note containing a stale `[[<deleted-id>]]` will re-parse and emit no edge.

## Atomicity

SQLite handles intra-database atomicity. The remaining concern is the cross-boundary write between the authored note file and the SQLite transaction.

Order: file first, database second. The insert/update flow writes the authored file (temp-and-rename, atomic per-file) before opening the SQLite transaction. The two failure modes:

- File write succeeds, SQLite transaction fails: the authored note exists with no database entry. Repair-on-startup or repair-on-read detects orphaned files and reconciles by re-running the indexing flow.
- File write fails: nothing changed. Caller sees an error; both file system and database remain unchanged.

The reverse order (SQLite first, file second) is rejected because a SQLite commit followed by a failed file write would leave a row pointing at content that doesn't exist — worse failure mode than a file with no row.

Source of truth: the authored note at `<corpus_root>/docs/<id>` is authoritative for body content. The `labels` membership in SQLite is authoritative for what labels a node carries. Conflicts between the FTS index and the file body get reconciled by rebuilding FTS from the file content during repair.

## Search day one

`hoplite_match_nodes(predicate, limit)` runs a single FTS5 query:

```sql
SELECT id, summary, score
FROM (
  SELECT
    nodes_fts.id,
    nodes_fts.summary,
    bm25(nodes_fts) AS score
  FROM nodes_fts
  WHERE nodes_fts MATCH ?
  ORDER BY score
  LIMIT ?
);
```

Then a second query fetches labels for the resulting ids. The whole match call is one or two SQLite queries.

FTS5's BM25 scoring uses default parameters (`k1 = 1.2`, `b = 0.75`). The implementation can override via `bm25(nodes_fts, weight_id, weight_body, weight_summary)` if column weighting matters; default weights are fine day one.

No per-call rescoring of every node. The FTS index is incremental — `INSERT` / `DELETE` / `REPLACE` in the write flow keep it current.

## Soft reindex via the agent

No batch server-side reindex pass day one. The agent-as-driver pattern covers the soft-reindex case through `hoplite_index_node(id)`: walk `<corpus_root>/docs/`, call `hoplite_index_node` on each file, and the write-time flow re-reads the body, re-parses wiki-links, regenerates the cached summary, recomputes the MinHash signature, materializes fresh `:related` edges, rewrites the relational rows, and refreshes the FTS index. Stale rows, hand-edited bodies, missing signatures, and missing derived metadata fix themselves through normal `hoplite_index_node` calls.

Embedding generation (Ollama-driven vector embeddings, used to supplement BM25 with cosine similarity and to derive additional `:related` edges) is on the [roadmap](roadmap.md#server-side-reindex-pass).

## Bootstrap — shipped envelope files

Four envelope files ship as bundled plugin assets. `hoplite_init_corpus` copies them into place on first run:

- `<cwd>/.hoplite/envelopes/read.md`
- `<cwd>/.hoplite/labels/instruction.md`
- `<cwd>/.hoplite/labels/reference.md`
- `<cwd>/.hoplite/labels/observation.md`

The corresponding `labels` rows (with `has_envelope = 1`) get inserted in the same init transaction. The exact prose for each envelope is in [behavior.md](behavior.md#day-one-envelope-prose).

After init the files are editable like any other authored file — by hand, or via `hoplite_apply_framing` for the three framing-axis envelopes. `hoplite_apply_framing` writes the file and updates `labels.has_envelope` in a single transaction.

The read content envelope (the one `hoplite_read_node` applies) is structurally separate; only edits through hand-edit or repair.

## Failure modes

### Mid-flight crashes

A single `hoplite_insert_node` or `hoplite_update_node` touches one file plus one SQLite transaction (the latter wrapping all relational changes). A `hoplite_delete_node` is similar.

SQLite's WAL mode handles transaction durability. A crash during a transaction rolls back automatically on next startup. Per-file writes use temp-and-rename so the authored note never appears half-written.

The cross-boundary failure mode is small: file written but database commit failed, or vice versa. Repair-on-startup detects orphans on either side:

- Files in `<corpus_root>/docs/` (walked recursively) with no corresponding `nodes` row → re-index the orphan via the `hoplite_index_node` flow.
- `nodes` rows with no corresponding authored file → drop the row (the file was deleted out-of-band, or the database survived a delete that the file didn't).
- Labels in `labels` with no members and no envelope file → drop the row (the last member left, no envelope was authored).

### Read failures

- Missing id: `hoplite_invoke_node`, `hoplite_read_node`, `hoplite_traverse_nodes(from_=missing)` return an error. "Missing" means no row in `nodes`.
- Missing authored file with `nodes` row present: surfaces as an error; the database expects a file that isn't there. Auto-repair drops the `nodes` row, or the operator restores the file. Deferred to repair.
- Corrupt database: SQLite usually recovers via WAL replay. If the database is unrecoverable, the operational `repair --rebuild` walks every authored file and rebuilds the database from scratch. The corpus is fully self-describing from `<corpus_root>/docs/` + `<corpus_root>/.hoplite/labels/` + `<corpus_root>/.hoplite/envelopes/read.md`.
- Dangling out_edge target: `hoplite_invoke_node(target)` returns an error when the reader follows the edge. The indexer doesn't pre-validate edge targets at read time.

### Concurrency

Day one assumes a single writer. SQLite in WAL mode already supports one writer plus many concurrent readers without blocking, so multi-reader is free at the database layer. Multi-writer support is on the [roadmap](roadmap.md#multi-writer-support).

### Inconsistency recovery

When the database disagrees with the authored corpus, the corpus wins. An operational `repair(scope)` CLI handles recovery:

- For one node: re-read `<corpus_root>/docs/<id>`, re-derive labels and edges, rewrite the corresponding `nodes`, `edges`, `label_membership`, and `nodes_fts` rows in one transaction.
- For all nodes: walk `<corpus_root>/docs/` recursively, run the per-node repair for each. Drop any `nodes` row whose authored file is missing. Drop any `labels` row whose membership is empty and envelope file is absent.

Full-corpus repair is the "I broke the index" escape hatch — slow but always correct.

## Worked example — node row

The row in `nodes` for the mcp data-model spec page (id `mcp/data-model.md`):

```
id                 = "mcp/data-model.md"
summary            = "the entities the graph carries and the fields each one holds"
minhash_signature  = <512-byte BLOB — 128 32-bit hashes>
embedding_path     = NULL                       (set when embeddings land)
```

Its rows in `edges`:

```
source_id            | type      | target_id                       | confidence | source   | rationale
mcp/data-model.md    | mentions  | mcp/tool-api.md                 |            |          |
mcp/data-model.md    | mentions  | mcp/behavior.md                 |            |          |
mcp/data-model.md    | related   | mcp/implementation-sqlite-hybrid.md | 0.62   | minhash  |
```

Its rows in `label_membership`:

```
label  | member_id
mcp    | mcp/data-model.md
```

The `mcp` label is auto-derived from the first path segment. The authored content lives at `<corpus_root>/docs/mcp/data-model.md` — pure markdown, no frontmatter.

## Worked example — label with envelope and members

The row in `labels`:

```
id            = "instruction"
summary       = "operative guidance the agent should follow"
has_envelope  = 1
```

The envelope prose at `<corpus_root>/.hoplite/labels/instruction.md`:

```markdown
The following is operative guidance for your current task. Apply it directly to your next response. Read it as you would read an active section of your system prompt — not as background reading, not as one perspective among many.
```

The rows in `label_membership`:

```
label        | member_id
instruction  | mcp/hoplite-skill.md
instruction  | notes/taking-notes.md
instruction  | notes/writing-prose.md
```

## Migration

Legacy-corpus migration is on the [roadmap](roadmap.md#migration-of-legacy-corpus). Day-one development uses a fresh empty corpus or a hand-curated subset.

## Rename semantics

Id change (which is also a file move) is one SQLite transaction plus file operations:

- Open transaction:
  - `UPDATE nodes SET id = ? WHERE id = ?`
  - `UPDATE edges SET source_id = ? WHERE source_id = ?`
  - `UPDATE edges SET target_id = ? WHERE target_id = ?`
  - `UPDATE label_membership SET member_id = ? WHERE member_id = ?`
  - `UPDATE nodes_fts SET id = ? WHERE id = ?` (or DELETE + INSERT)
  - Commit.
- Rename the authored file: `mv <corpus_root>/docs/<old-id> <corpus_root>/docs/<new-id>` (atomic). Create any intermediate folders the new id requires.
- Grep the corpus for `[[<old-id>]]` references and rewrite them.

A `rename_node(old, new)` MCP call is a natural candidate for the indexer's surface — particularly because an id change may also change the first path segment, which changes the auto-derived label.

