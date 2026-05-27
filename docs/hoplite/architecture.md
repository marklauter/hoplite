---
title: Architecture
summary: The Hoplite system as it is — corpus, graph, walker, FTS5, MinHash, dump schema, error model. One document covering the day-one shape end to end.
tags: [hoplite, mcp, architecture]
created: 2026-05-25
---

## Overview

Hoplite is an in-memory property graph over a corpus of markdown documents. The `.md` files under `docs/` are the only persistent state. At MCP server startup a two-pass walker rebuilds the graph from frontmatter and body content; everything else — properties, edges, MinHash signatures, the FTS5 text index, alias and casefold lookup tables — is derived and held in RAM.

The agent reads document bodies through its own file tools (`Read`, `Write`, `Edit`, `Bash`). Hoplite serves four query tools — `where`, `relatives`, `refresh`, `export` — over the in-memory graph. There is no CRUD surface on Hoplite itself; the markdown file on disk is the source of truth, and `refresh` picks up whatever's there.

This document covers the system as one piece. Tool signatures and the 4-tool API live in [[docs/hoplite/tool-api.md|tool-api.md]]; deferred features in [[docs/hoplite/roadmap.md|roadmap.md]].

## The corpus

A Hoplite corpus is a directory of `.md` files. The MCP server roots itself at the working directory when spawned; every file matching `**/*.md` under that root is a candidate document. Subdirectory structure is presentational — `docs/notes/coffee.md` and `docs/journal/2026-05-25-1430-roast.md` are both documents, identified by their relative paths.

The corpus is fully Obsidian-compatible — same frontmatter shape, same `[[wikilink]]` syntax, same tag convention. Hand-edits in Obsidian and writes by agents are indistinguishable from Hoplite's view; both round-trip through `refresh`.

## Frontmatter — the YAML envelope

Every document opens with a YAML frontmatter block delimited by `---` fences. Four fields are mandatory:

- `title` (string) — short, human-readable name.
- `summary` (string) — one-line lede. Returned by the query tools so callers scan candidates without opening files.
- `tags` (list of strings) — kebab-case slugs. Empty list (`tags: []`) is fine.
- `created` (ISO date string, `YYYY-MM-DD`) — creation date.

Optional fields:

- `aliases` (list of strings) — alternate paths that resolve to this document. Omit when empty; add on rename so wikilinks pointing at the old name still resolve.

Arbitrary user-defined keys pass through unchanged. `status: draft`, `priority: high`, `due: 2026-06-01` — Hoplite stores them; tools like Obsidian and Dataview read them.

`updated` is intentionally absent. Modification time derives from git history when callers need it — `mtime` lies after git checkouts and file copies, frontmatter drifts from reality, git is authoritative.

A document with missing or unparseable frontmatter, or any mandatory field absent, is skipped from the graph and surfaced as a warning on the next reindex. The walker synthesizes no defaults.

## The graph

The graph carries one node type and two edge kinds. Everything authored in frontmatter — including tags — is a property on the owning document.

### Documents

A `Document` represents one markdown file, identified by its repo-relative path (including the `docs/` root segment). File-level fields:

- `path` — repo-relative path starting with `docs/` and ending in `.md` for real documents; `ghost/<slug>` for intentional open loops. The document's identity within the runtime graph and the value returned to query callers.
- `resolved` — `true` for files that exist on disk; `false` for ghost documents.
- `content_hash` — sha256 of the body. Used for staleness detection on reindex. Null on ghosts.
- `minhash` — 1024-byte MinHash signature (128 × uint64). Computed at startup; held in RAM, never persisted. Null on ghosts.

Bodies live in the markdown file on disk. The walker reads bodies during indexing to tokenize for FTS5 and compute MinHash signatures, then discards them — body is never persisted in the graph or the dump. To read a body, `Read` the file at the document's `path`.

### Properties

Every YAML frontmatter field — mandatory (`title`, `summary`, `tags`, `created`), optional (`aliases`), and user-defined (`status`, `priority`, anything) — becomes a property on the owning document. Properties are key-value pairs in EAV form: one row per `(path, key, value)` triple. Array-valued fields like `tags: [hoplite, note]` produce one row per element.

Properties never appear as edge endpoints. Edges connect documents to documents; properties describe what a document is.

### Edges

Two edge kinds, closed set. Edges connect documents to documents only.

- `mentions` — document → document. Materialized from `[[wikilink]]` references in body text. The walker emits one edge per `(source, target)` pair regardless of how many wikilinks point at the target; the graph records relationships, not occurrences.
- `related` — document ↔ document, symmetric. Materialized from pairwise MinHash similarity above a configured threshold. Both directions emitted as two edge rows. Carries a `confidence` property holding the Jaccard score.

Use cases for richer relations (`cites`, `contradicts`, `requires`, `see-also`) express through `mentions` plus body prose. No aspirational edge types reserved.

Edges carry identity (`id`) plus the `(src, dst, kind)` triple as a UNIQUE constraint. Edge metadata beyond that lives in edge properties, following the same EAV pattern as node properties. Day one, only `related` edges carry a property (`confidence`); the symmetric edge-property table exists so future annotations slot in without schema change.

## Wikilinks and ghost documents

Body text uses Obsidian's wikilink syntax: `[[target]]`. Two shapes are valid:

- `[[docs/<path>.md]]` — a real cross-reference. The target is the full repo-relative path including the `docs/` root and the `.md` extension. `where` and `relatives` return that same path in their `path` field, so a downstream agent can `Read` the file directly without rebasing. An alias declared in some document's `aliases` list resolves too. Resolution is case-insensitive ordinal — `[[Docs/Notes/Foo.MD]]` and `[[docs/notes/foo.md]]` reach the same target.
- `[[ghost/<slug>]]` — an intentional open loop. The author knows the document doesn't exist; the `ghost/` prefix declares the intent. Ghost documents are first-class graph entities with `resolved = false`, no body, no properties. Inbound `mentions` edges point at the ghost as if it were real.

Anything else is malformed. The reindex pass validates every extracted target and appends a warning to `WriteResult.warnings` if a wikilink starts with neither `docs/` nor `ghost/` — the link is skipped rather than silently producing a garbage-shaped ghost. Sample wikilinks in prose live inside backticks (` ` ` ` or ``` ` ``` ` ``` `) so the extractor masks them; this convention is described in the prose component.

When a file at the matching `docs/...` path is later added and reindex runs, a ghost referenced at that path is promoted in place: identity stays stable, file-level fields fill in, properties populate from the new frontmatter, every inbound edge already points at the right node. Promotion across the `docs/` ↔ `ghost/` boundary is the author's job — rewrite the wikilink from `[[ghost/<slug>]]` to `[[docs/<path>.md]]` when the file lands.

The ghost set is queryable as the agent's "open loops" backlog — documents referenced but not yet written.

Wikilinks are never silently dropped except for malformed targets. A `docs/`-shaped target that resolves becomes a real-to-real edge; one that doesn't becomes a real-to-ghost edge keyed at the authored path. A `ghost/`-shaped target always becomes a real-to-ghost edge keyed under `ghost/<slug>`.

## External references

Inline markdown links `[text](https://...)` are first-class graph signal alongside wikilinks. The walker's pass 2 matches every body-text occurrence of the pattern where the URL begins with `http://` or `https://`, registers the URL as a graph node keyed by the verbatim URL string, and emits a `cites` edge from the source document to that node. Multiple links from one document to the same URL collapse to one edge.

URL nodes carry `resolved = false`, no frontmatter, no body, no FTS row — they're terminal. Discoverable through `relatives(predicate={"edge_types": ["cites"]})` from a containing document, never through `where` text search. The URL itself is the path, so a caller that gets a `cites` edge can `WebFetch` the URL or include it in another document's prose verbatim.

No canonicalization. `https://example.com/`, `https://example.com`, and `http://example.com` are three distinct nodes — author authority. Same convention as wikilinks: matched-pair `[text](url)` markdown links inside backticks or fenced blocks are masked and skipped, so sample URLs in prose don't pollute the graph.

The walker injects a synthetic `url` tag on every URL node and a synthetic `ghost` tag on every ghost node. Real documents author their own tags through frontmatter; unresolved nodes have no frontmatter, so the walker tags them by category. `where({"tagged": "url"})` enumerates every external URL the corpus cites; `where({"tagged": "ghost"})` enumerates every intentional open loop. Tag-only queries skip the FTS-resolved-only restriction — the no-text branch surfaces ghosts and URLs alongside real documents.

For durable external references that earn metadata (tags, summary, "why this matters") or are reused across multiple documents, the convention is a proxy note at `docs/proxies/<slug>.md` carrying the URL via a markdown link plus context in the body. Other documents wikilink the proxy; the proxy emits the `cites` edge to the URL. Backlinks (`relatives` with `direction="in"`) over the proxy then show every doc that referenced the resource.

## Tag predicates

The two query tools accept a tag predicate that filters which documents appear in results.

Grammar:

```
expr     ::= or_expr
or_expr  ::= and_expr ( '|' and_expr )*
and_expr ::= not_expr ( '&' not_expr )*
not_expr ::= '!' not_expr | atom
atom     ::= slug | '(' expr ')'
slug     ::= [a-z0-9-]+
```

Operators: `&` intersection, `|` union, `!` exclusion, `(...)` grouping. Precedence: `!` > `&` > `|`, left-associative.

Examples:

- `hoplite` — documents tagged `hoplite`.
- `note & hoplite` — documents tagged both.
- `(note | journal) & !draft` — notes or journal entries, excluding drafts.

Predicates apply as a post-filter on results. For `where`, the predicate narrows the BM25-scored candidate list. For `relatives`, the walk follows edges per the edge predicate; the tag predicate filters which reached documents appear in the result. Non-matching intermediate documents are still traversed through.

## The walker

`refresh` runs the walker. The graph is rebuilt from scratch on every reindex — no incremental updates day one. At hundreds-to-low-thousands corpus scale, full rebuild is the simplest correct behavior.

### Pass 1: identity collection

Glob `**/*.md` under the corpus root. For each file:

1. Read the YAML frontmatter block.
2. Parse the four mandatory fields plus any optional or user-defined fields. Skip and warn on missing or unparseable frontmatter.
3. Register the document under its repo-relative `docs/...` path; register each alias; populate the casefold index for both canonical path and aliases.

After pass 1, every real document is known and every alias resolves. The lookup table is complete before any wikilink is parsed — required because pass 2's wikilink resolution depends on knowing every canonical and alias up front.

### Pass 2: body load, edges, indexes

For each registered document:

1. Read the body (everything after the closing `---` fence).
2. Compute the sha256 content hash; store on the document.
3. Parse `[[wikilink]]` references. Reject any target that doesn't start with `docs/` or `ghost/` — append a warning, skip the link. For valid targets, resolve via the casefold → alias → canonical-path chain. Resolved `docs/...` targets get a `mentions` edge to the real document; unresolved `docs/...` targets and all `ghost/...` targets materialize a ghost keyed at the authored path and get a `mentions` edge to it. Multiple wikilinks from one document to the same target collapse to a single edge.
4. Materialize node properties from the frontmatter — one row per scalar field, one row per array element for `tags` and `aliases` and any other multi-value key.
5. Compute the MinHash signature of the body. Store on the document.
6. Insert into the in-memory FTS5 table: `(path, title, summary, body)`.

### Aggregate pass: `related` edges

After pass 2, run pairwise MinHash similarity:

1. For every pair of resolved documents `(d1, d2)` where `d1 < d2` (path-ordered to avoid double-counting), compute Jaccard similarity from the two MinHash signatures.
2. If similarity exceeds the configured threshold (default `0.20`), emit two `related` edges — `(d1, d2)` and `(d2, d1)` — each carrying `confidence = <score>` as an edge property.

Pairwise scan is O(N²) but cheap at scale — 128-int Jaccard comparisons run in ~100ms for 1000 documents. LSH bucketing is the optimization to reach for past 10⁵ documents; see [[docs/hoplite/roadmap.md|roadmap.md]].

## Text search — FTS5 and BM25

Hoplite holds an in-memory `:memory:` SQLite database with one FTS5 virtual table for BM25 scoring:

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

`where` runs:

```sql
SELECT path, summary, bm25(fts) AS score
FROM fts
WHERE fts MATCH ?
ORDER BY score
LIMIT ?
```

BM25 default parameters: `k1 = 1.2`, `b = 0.75`. The tag predicate, if supplied, applies as a Python-level post-filter against each candidate's tag properties.

The FTS5 connection lives inside `Graph.fts` for the server's lifetime. It's never persisted; on every reindex it's torn down and rebuilt.

## MinHash signatures

Signatures are 128 × uint64 (1024 bytes) per document. The hash family derives `k` independent hash functions from a base hash via universal hashing modulo Mersenne prime `M_61 = 2^61 - 1`: `h_i(x) = (a_i * base_hash(x) + b_i) mod M_61` for fixed constants `a_i, b_i`.

Configuration knobs:

- `minhash_signature_size` (default 128)
- `minhash_shingle_size` (default 5) — word n-gram width
- `minhash_threshold` (default 0.20) — minimum Jaccard for `related` edge materialization

Signatures live as `bytes` on the `Document` dataclass. Never persisted; recomputed at every startup. Cold-start cost is ~50ms per document, dominating walker time at 1000-doc corpora (~50s total).

Cold-start budget at 1000 documents (~5KB average body):

- Walk + body load: ~150ms (read ~5MB from SSD)
- FTS5 populate: ~500ms (C-backed tokenization)
- MinHash compute: ~50s (dominant cost)
- Pairwise MinHash for `related`: ~100ms

Total: ~50s. Scales roughly linearly; 100 docs ≈ 5s, 5000 docs ≈ 5 minutes. The cost is decision-reversible — if corpora grow past tolerable startup time, a persistent `.hoplite/cache.db` for MinHash signatures returns without changing the rest of the architecture.

## Reindex semantics

`refresh()` rebuilds the in-memory graph from the current corpus state. Day one this is the only way to pick up file changes — there's no automatic detection of edits between calls. An agent that writes a file calls `refresh` afterward. Hand-edits in Obsidian show up after the next reindex call.

The server initializes the graph at startup by running the walk implicitly — same code path as a reindex call. No init tool, no init-mode gate; the graph is ready to serve as soon as the walk finishes.

Per-query stat-checking is the most-likely future upgrade (see [[docs/hoplite/roadmap.md|roadmap.md]]).

## Dump schema

`export(path=None)` snapshots the in-memory graph to a SQLite file for SQL-level debugging. Default destination is `.hoplite/<ISO-timestamp>.index.sqlite` relative to the corpus root, with timestamp `YYYY-MM-DDTHH-MM-SS` (colons replaced for Windows). Each dump produces a uniquely-named file; prior snapshots survive on disk.

The schema mirrors the in-memory `Graph` shape one-to-one. The whole point of the export is to see exactly what's in memory; the dump adds no indirection the runtime doesn't already carry.

```sql
CREATE TABLE documents (
  path TEXT PRIMARY KEY,
  resolved INTEGER NOT NULL,
  content_hash TEXT,
  minhash BLOB
);

CREATE TABLE node_properties (
  path TEXT NOT NULL REFERENCES documents(path),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (path, key, value)
);
CREATE INDEX idx_node_props_key_value ON node_properties(key, value);

CREATE TABLE edges (
  src TEXT NOT NULL REFERENCES documents(path),
  dst TEXT NOT NULL REFERENCES documents(path),
  kind TEXT NOT NULL,
  PRIMARY KEY (src, dst, kind)
);
CREATE INDEX idx_edges_src ON edges(src);
CREATE INDEX idx_edges_dst ON edges(dst);

CREATE TABLE edge_properties (
  src TEXT NOT NULL,
  dst TEXT NOT NULL,
  kind TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (src, dst, kind, key, value),
  FOREIGN KEY (src, dst, kind) REFERENCES edges(src, dst, kind)
);
CREATE INDEX idx_edge_props_key_value ON edge_properties(key, value);

CREATE VIRTUAL TABLE fts USING fts5(
  path UNINDEXED,
  title,
  summary,
  body,
  tokenize = 'porter unicode61',
  content = ''  -- contentless: only the inverted index survives
);
```

Notes:

- Paths are the natural keys throughout. `documents.path` ↔ `Graph.documents` (the in-memory dict's key). `node_properties.path` ↔ entries in `Graph.node_properties`. The composite `(src, dst, kind)` on `edges` and `edge_properties` ↔ `Graph.out_edges` / `Graph.edge_properties`. No synthetic integer IDs at runtime or in the dump.
- `documents.resolved` flags ghost/URL/real. Ghosts (`path` starting with `ghost/`) have `resolved = 0`, `content_hash` and `minhash` `NULL`, and a synthetic `tags: ['ghost']` row in `node_properties`. URL nodes (`path` starting with `http://`/`https://`) have the same shape but with `tags: ['url']`.
- Bodies are not stored. FTS5 is declared `content=''` (contentless mode): the inverted index is built from titles, summaries, and bodies at insert time, but the raw text is discarded. Match queries work; column reads do not. To read a body, `Read` the file at its `path`. FTS joins back to `documents` via the `path` column.
- `node_properties` holds every frontmatter field — `title`, `summary`, `created`, `tags`, `aliases`, and any user-defined keys. Array fields produce one row per element. SQLite type-affinity preserves authored type — `priority: 5` stores `5` as integer even though the column is declared TEXT.
- Inverted lookups ("which paths have `key='tags' AND value='hoplite'`?") run against `idx_node_props_key_value`. The forward direction (start from a known path) uses the PRIMARY KEY. Same rows, different B-tree orderings.
- Edges hold only identity and topology. Everything else, including `confidence` on `related` edges, rides in `edge_properties` keyed on the same `(src, dst, kind)` triple as the edge it annotates.
- A polymorphic-node `nodes(id, kind)` table is *not* present. The path prefix (`docs/`, `ghost/`, `http://`, `https://`) is the kind discriminator at both layers; specialization tables can be added the day a node kind earns columns of its own.

The dump operation opens the destination, drops any prior tables (so the file is fully overwritten), runs the DDL above, bulk-inserts from the in-memory dicts, and returns a `WriteResult` with the absolute output path and row counts per entity.

## Error model

Two failure modes, distinguished by remediability:

- **Invariant violations throw exceptions.** Programming errors the caller could have prevented — `None` for a required string, out-of-range integer, malformed predicate. Throwing surfaces the bug.
- **Constraint violations return warnings in the result.** Runtime conditions the caller couldn't have known — a document with malformed frontmatter, a `dump_index` destination the server can't write to.

At the MCP wire boundary, both land as content responses. Thrown exceptions become structured error content with `isError: true`. Constraint warnings ride along inside successful results in the `warnings` field of `WriteResult`. JSON-RPC protocol errors stay reserved for transport failures.

Specific failure modes:

- **Frontmatter parse failures** — the document is skipped from the graph and surfaced as a warning. Fix the YAML and re-run reindex.
- **Wikilinks to ghosts** — not a failure mode. The ghost materializes; the edge points at it; the unresolved set is queryable as open loops.
- **Server crash** — the corpus on disk is untouched; the next startup rebuilds the graph from scratch. No recovery, no repair tool.
- **Dump destination unwritable** — `export` validates the path before writing; an unwritable path surfaces as `isError: true`.
- **Out-of-date graph** — the in-memory graph reflects state as of the last reindex. Files written between calls show up after the next `refresh`.

## Concurrency

Single writer, single reader, single server process. The in-memory graph isn't safe for concurrent mutation; the MCP server's single-threaded request handler is the lock. Multi-writer support is deferred ([[docs/hoplite/roadmap.md|roadmap.md]]).
