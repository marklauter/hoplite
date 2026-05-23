# SQLite-hybrid implementation

[Implementation, alternative] How the contracts map onto SQLite for the relational layer with files for the prose layer.

## Overview

Notes, label envelope prose, the read envelope, and embedding blobs stay as files. Everything relational — node metadata, label metadata, label memberships, edges — lives in a single SQLite database. Search uses SQLite's FTS5 virtual table; no per-call BM25 recomputation.

The tool API surface (see [tool-api.md](tool-api.md)) is identical to the file-based implementation. Behavior contracts (see [behavior.md](behavior.md)) hold unchanged. Only the persistence layer changes.

## Storage layout

```
docs/notes/<slug>.md                            authored note (pure markdown, body only)
docs/notes/<iso-date>-<slug>.md                 authored note with observation or journal label
docs/index/graph.db                             SQLite database (all relational data)
docs/index/labels/<label>.md                    label envelope (pure markdown, optional prose)
docs/index/envelopes/read.md                    fixed content envelope applied by read()
docs/index/embeddings/<id>.npy                  embedding blob (when reindex lands)
```

File responsibilities:

- `.md` files carry human-readable content — authored notes and envelope prose.
- `.npy` files carry binary embedding vectors.
- `graph.db` carries every structured query target: nodes (metadata), labels (metadata), label memberships, edges, and the full-text search index.

What's gone from the file-based shape: per-node `.yml` sidecars, per-label `.yml` sidecars, membership marker files, and the `docs/index/labels/<label>/` member folders. All collapse into SQLite rows.

## Database schema

```sql
CREATE TABLE nodes (
  id              TEXT PRIMARY KEY,
  summary         TEXT NOT NULL,
  embedding_path  TEXT
);

CREATE TABLE labels (
  id              TEXT PRIMARY KEY,
  summary         TEXT,
  has_envelope    INTEGER NOT NULL DEFAULT 0  -- 1 if docs/index/labels/<id>.md exists
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

WAL mode is enabled at startup for safe single-writer concurrency and read-during-write.

## Entity-to-storage mapping

How each entity from [data-model.md](data-model.md) is realized.

### Node

Two locations per node:

- Authored content: `docs/notes/<id>.md`. Pure markdown body, no YAML frontmatter. Body shape on lines 1-4 is fixed: `# Title` on line 1, blank on line 2, summary on line 3, blank on line 4, body sections from line 5 onward.
- Metadata: one row in `nodes` (`id`, `summary`, `embedding_path`) plus rows in `edges` for each outbound edge. The body text is indexed in `nodes_fts` for `match`.

The two stores hold disjoint primary concerns: the file is the source of truth for body content; the database is the source of truth for metadata, edges, and the search index.

### Label

Up to two locations per label:

- One row in `labels` (`id`, optional `summary`, `has_envelope` boolean).
- Optional `docs/index/labels/<label>.md` carrying envelope prose. The `has_envelope` column tracks whether the file exists; the file is authoritative.
- Rows in `label_membership` for each member.

Membership IS a relational table. Adding a node to a label is one `INSERT OR IGNORE`. Removing is one `DELETE`. Listing members is one query.

### Edge

Each edge is a row in `edges`. Symmetric `:related` edges are written as two rows (one in each direction), or queried bidirectionally via the `idx_edges_target` index — the implementation can choose either approach; the symmetry is now a query property, not a denormalization concern.

### Envelope

The framing component for `invoke` comes from `docs/index/labels/<label>.md` (the label envelope file). For `read`, from `docs/index/envelopes/read.md`. The structured `Envelope` shape is composed by the server at retrieval time; on disk it's just the envelope file plus the structure built in memory.

## Id and filename rules

A node's id is its authored filename without the `.md` extension. The filename and the `nodes.id` column always agree.

Filename convention. Nodes carrying `observation` or `journal` labels use the ISO date prefix — `docs/notes/<iso-date>-<slug>.md`. The indexer parses the prefix to derive the date label. Other nodes use `docs/notes/<slug>.md`. No separate `date:` column — the prefix is the date.

Date label is derived only when the node carries `observation` or `journal`. Removing both labels drops the date label on the next write; the prefix becomes cosmetic.

Slug derivation matches the canonical rule (lowercase, whitespace to hyphens, strip non-alphanumeric except hyphens).

## Corpus root configuration

The MCP server reads a `corpus_root` config value at startup. The database path is `<corpus_root>/docs/index/graph.db`. All other paths derive from `corpus_root` the same way as in the file-based implementation.

## Why this shape

SQLite handles every relational concern the filesystem was emulating:

- Per-label membership becomes a real indexed join table. "All nodes labeled X" is a single SELECT, fast at any corpus size.
- Bidirectional indexes — `idx_membership_member` and `idx_edges_target` let both "what labels does this node carry" and "what edges point at this node" run as indexed queries.
- Edges become a first-class table. Symmetric `:related` edges, traversal predicates, and confidence filtering all map to standard SQL.
- ACID transactions across the whole graph state. A single `insert` or `update` commits all node, edge, and membership changes atomically. No cross-file atomicity story to engineer.
- FTS5 gives BM25 search natively. No per-call rescoring; the index is incremental.

Prose stays in files for the same reasons it does in the file-based implementation:

- Notes are greppable, git-diffable, and hand-editable.
- Label envelope prose and the read envelope are content the agent (and the user) authors directly; their natural medium is markdown files.
- Embedding blobs are binary; SQLite BLOBs work but `.npy` files are more interoperable with ML tooling.

## Insert and update flow

What `insert(id, body, labels, out_edges)` and `update(id, body, labels, out_edges)` do, in order.

0. Existence check. `insert` rejects if a row exists in `nodes` for the id (and rejects if `docs/notes/<id>.md` exists, as a belt-and-braces safety check). `update` rejects if no row exists.
1. Validate labels. Per [behavior.md](behavior.md#validation-and-error-model).
2. If labels include `observation` or `journal`, verify the id has an ISO date prefix. Reject if missing.
3. Validate `out_edges`. Reject any author-supplied edge that carries a `source` field.
4. Write the authored note to `docs/notes/<id>.md` (temp-and-rename for atomicity). Pure markdown, no frontmatter.
5. Parse `[[wiki-links]]` from the body; build the `:mentions` edges.
6. Reconcile `out_edges` per the rule in [behavior.md](behavior.md#edge-reconciliation-on-update). On `insert`, no prior state — just merge parsed mentions with author-supplied. On `update`, preserve derived edges by querying the existing `edges` table for rows with `source` set and merging them in.
7. Compose auto-derived labels: `note`, plus the ISO date label if applicable.
8. Parse the cached summary from the body — line 3.
9. Open a SQLite transaction:
   - `INSERT OR REPLACE` into `nodes` with id, summary, embedding_path.
   - `DELETE FROM edges WHERE source_id = ?` then `INSERT` the reconciled edge set.
   - `DELETE FROM label_membership WHERE member_id = ?` (clears prior memberships on update; no-op on insert).
   - For each label the node carries: `INSERT OR IGNORE INTO labels (id, has_envelope) VALUES (?, COALESCE((SELECT has_envelope FROM labels WHERE id=?), 0))` then `INSERT INTO label_membership (label, member_id) VALUES (?, ?)`.
   - Refresh the FTS index: `DELETE FROM nodes_fts WHERE id = ?` then `INSERT INTO nodes_fts (id, body, summary) VALUES (?, ?, ?)`.
   - Commit.
10. Return `WriteResult` with id and any warnings.

The SQLite transaction in step 9 is atomic — every relational change for this write succeeds or none do. The file write in step 4 is a separate atomic operation; cross-boundary failure modes are covered in [Atomicity](#atomicity) below.

## Delete flow

What `delete(id)` does:

1. Existence check. Reject if no row in `nodes` for the id.
2. Unlink `docs/notes/<id>.md`.
3. Open a SQLite transaction:
   - `DELETE FROM edges WHERE source_id = ? OR target_id = ?` (drops outgoing edges; also drops back-references in derived edges pointing at this id, since the row is going away).
   - `DELETE FROM label_membership WHERE member_id = ?`.
   - `DELETE FROM nodes_fts WHERE id = ?`.
   - `DELETE FROM nodes WHERE id = ?`.
   - Commit.

Wiki-link references in other notes' bodies still exist as raw `[[...]]` text but resolve to nothing — the broken-link semantic still applies. The next `update` to a note containing a stale `[[<deleted-id>]]` will re-parse and emit no edge.

## Atomicity

SQLite handles intra-database atomicity. The remaining concern is the cross-boundary write between the authored note file and the SQLite transaction.

Order: file first, database second. The insert/update flow writes the authored file (temp-and-rename, atomic per-file) before opening the SQLite transaction. The two failure modes:

- File write succeeds, SQLite transaction fails: the authored note exists with no database entry. Repair-on-startup or repair-on-read detects orphaned files and reconciles by re-running the indexing flow.
- File write fails: nothing changed. Caller sees an error; both file system and database remain unchanged.

The reverse order (SQLite first, file second) is rejected because a SQLite commit followed by a failed file write would leave a row pointing at content that doesn't exist — worse failure mode than a file with no row.

Source of truth: the authored note at `docs/notes/<id>.md` is authoritative for body content. The `labels` membership in SQLite is authoritative for what labels a node carries (no folder marker analog). Conflicts between the FTS index and the file body get reconciled by rebuilding FTS from the file content during repair.

## Search day one

`match(predicate, k)` runs a single FTS5 query:

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

## Reindex — deferred, not forgotten

Same shape as the file-based implementation. The agent-as-driver pattern (walk notes, call `update` on each) does soft-reindex without a server-side pass. The features needing a server-side reindex are:

- MinHash pairwise relatedness — Jaccard-similarity edges above `minhash_threshold` materialize as `:related` derived edges with `source: minhash`. Adds rows to `edges` in batches.
- Embedding generation via Ollama — writes `.npy` files into `docs/index/embeddings/` and populates `nodes.embedding_path`.

A bulk reindex pass is much faster than under the file-based implementation: one SQLite transaction can insert thousands of `:related` edges without thousands of filesystem operations.

## Bootstrap — shipped envelope files

Four envelope files arrive as bundled assets the plugin installer drops into place at install time:

- `docs/index/envelopes/read.md`
- `docs/index/labels/instruction.md`
- `docs/index/labels/reference.md`
- `docs/index/labels/observation.md`

The corresponding `labels` rows (with `has_envelope = 1`) are inserted by a first-run migration when the server starts and notices the file. The exact prose for each envelope is in [behavior.md](behavior.md#day-one-envelope-prose).

After install they're editable like any other authored file — by hand, or via `apply_framing` for the three framing-axis envelopes. `apply_framing` writes the file and updates `labels.has_envelope` in a single transaction.

The `read` envelope is structurally separate; only edits through hand-edit or repair.

## Failure modes

### Mid-flight crashes

A single `insert` or `update` touches one file plus one SQLite transaction (the latter wrapping all relational changes). A `delete` is similar.

SQLite's WAL mode handles transaction durability. A crash during a transaction rolls back automatically on next startup. Per-file writes use temp-and-rename so the authored note never appears half-written.

The cross-boundary failure mode is small: file written but database commit failed, or vice versa. Repair-on-startup detects orphans on either side:

- Files in `docs/notes/` with no corresponding `nodes` row → re-index the orphan.
- `nodes` rows with no corresponding authored file → drop the row (the file was deleted out-of-band, or the database survived a delete that the file didn't).
- Labels in `labels` with no members and no envelope file → drop the row (the last member left, no envelope was authored).

### Read failures

- Missing id: `invoke`, `read`, `traverse(from=missing)` return an error. "Missing" means no row in `nodes`.
- Missing authored file with `nodes` row present: surfaces as an error; the database expects a file that isn't there. Auto-repair drops the `nodes` row, or the operator restores the file. Deferred to repair.
- Corrupt database: SQLite usually recovers via WAL replay. If the database is unrecoverable, the operational `repair --rebuild` walks every authored file and rebuilds the database from scratch. The corpus is fully self-describing from `docs/notes/` + `docs/index/labels/<label>.md` + `docs/index/envelopes/read.md`.
- Dangling out_edge target: `invoke(target)` returns an error when the reader follows the edge. The indexer doesn't pre-validate edge targets at read time.

### Concurrency

SQLite in WAL mode supports one writer plus many concurrent readers without blocking. Multi-reader is essentially free; multi-writer serializes through the SQLite write lock.

For multi-agent writes, SQLite's connection model handles serialization automatically — the MCP server can accept concurrent write calls and let SQLite queue them. No application-level locking needed.

The file-boundary remains: two writers updating the same authored note race on the file. The SQLite transaction can still commit cleanly for whichever wins, but the file may not match what the last-committed transaction expected. For day one, single-writer assumption stays; multi-writer support adds per-id file locking on the authored note, paired with SQLite's native transaction serialization.

### Inconsistency recovery

When the database disagrees with the authored corpus, the corpus wins. An operational `repair(scope)` CLI handles recovery:

- For one node: re-read `docs/notes/<id>.md`, re-derive labels and edges, rewrite the corresponding `nodes`, `edges`, `label_membership`, and `nodes_fts` rows in one transaction.
- For all nodes: walk `docs/notes/`, run the per-node repair for each. Drop any `nodes` row whose authored file is missing. Drop any `labels` row whose membership is empty and envelope file is absent.

Full-corpus repair is the "I broke the index" escape hatch — slow but always correct.

## Worked example — node row

The row in `nodes` for the data-model note:

```
id              = "mcp-server-as-skill-system-runtime"
summary         = "the MCP server as runtime for a knowledge-graph-backed skill system"
embedding_path  = "docs/index/embeddings/mcp-server-as-skill-system-runtime.npy"
```

Its rows in `edges`:

```
source_id                              | type        | target_id                                       | confidence | source   | rationale
mcp-server-as-skill-system-runtime     | mentions    | prototype-the-plugin-mcp-server-in-python       |            |          |
mcp-server-as-skill-system-runtime     | mentions    | writing-prose                                   |            |          |
mcp-server-as-skill-system-runtime     | related     | skill-composition-foundation-and-downstream     | 0.62       | minhash  |
```

Its rows in `label_membership`:

```
label         | member_id
note          | mcp-server-as-skill-system-runtime
architecture  | mcp-server-as-skill-system-runtime
mcp           | mcp-server-as-skill-system-runtime
skills        | mcp-server-as-skill-system-runtime
```

The authored content lives at `docs/notes/mcp-server-as-skill-system-runtime.md` — pure markdown, no frontmatter.

## Worked example — label with envelope and members

The row in `labels`:

```
id            = "instruction"
summary       = "operative guidance the agent should follow"
has_envelope  = 1
```

The envelope prose at `docs/index/labels/instruction.md`:

```markdown
The following is operative guidance for your current task. Apply it directly to your next response. Read it as you would read an active section of your system prompt — not as background reading, not as one perspective among many.
```

The rows in `label_membership`:

```
label        | member_id
instruction  | orchestrator-skill
instruction  | taking-notes
instruction  | writing-prose
```

## Migration — deferred

The current `docs/notes/` corpus predates the graph shape. Migration to the SQLite hybrid takes the same shape as migration to the file-based implementation: walk every note, derive labels from filenames and frontmatter, populate the database, write any necessary envelope files. Deferred — when migration lands, it runs as a one-time CLI pass.

Migration from the file-based implementation to SQLite hybrid is itself a defined operation: walk the file-based index (`.yml` sidecars + label folders), insert equivalent rows into SQLite, leave the authored notes and envelope files untouched. The reverse migration (SQLite → file-based) is symmetric: dump rows into `.yml` sidecars and recreate the label folders.

## Rename semantics

Slug change is one SQLite transaction plus two file operations:

- Open transaction:
  - `UPDATE nodes SET id = ? WHERE id = ?`
  - `UPDATE edges SET source_id = ? WHERE source_id = ?`
  - `UPDATE edges SET target_id = ? WHERE target_id = ?`
  - `UPDATE label_membership SET member_id = ? WHERE member_id = ?`
  - `UPDATE nodes_fts SET id = ? WHERE id = ?` (or DELETE + INSERT)
  - Commit.
- Rename the authored file: `mv docs/notes/<old>.md docs/notes/<new>.md` (atomic).
- Grep the corpus for `[[old]]` references and rewrite them.

A `rename_node(old, new)` MCP call is a natural candidate for the indexer's surface.

## YAML conventions

Not applicable to this implementation. The label envelope files are pure markdown; the authored notes are pure markdown. No YAML on disk for the indexer to parse. SQLite handles its own type system.
