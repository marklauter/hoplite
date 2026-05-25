---
title: Hoplite design decision log
summary: "[Log] Running record of design decisions from Hoplite design sessions. Append-only chronological list; superseded entries stay with a marker and pointer to what replaced them."
tags: [hoplite, mcp, log, decisions]
created: 2026-05-25
aliases: []
---

## 2026-05-24

### Lift title and summary out of body into YAML frontmatter
[ACTIVE]
The body-shape contract (H1 on line 1, blank on line 2, summary on line 3, blank on line 4) breaks for non-prose content — code, transcripts, fragments. Frontmatter is the standard pattern; Obsidian validates it. Title and summary become first-class metadata supplied by the agent at write time.

### Server-generated ULIDs as domain identifiers
[SUPERSEDED by: identity collapses to path]
Original surrogate-key proposal: server mints ULIDs, agent passes them in tool calls, edges reference ULIDs, filenames are mutable presentation.

### Three-tier identity model
[SUPERSEDED by: identity collapses to path]
rowid (SQLite join key) + ULID/permalink (domain ID) + filename (presentation). Justified by SQLite's foreign-key-stability needs.

### `ids.py` splits into `ulids.py` and `slugify.py`
[SUPERSEDED by: identity collapses to path]
Post-ULID code reorganization. Moot after the SQLite drop.

### Aliases on documents for rename continuity
[ACTIVE]
Obsidian-style alternate names that populate on rename so old wikilinks keep resolving. Smaller blast radius than body-rewrite-on-rename. Tooling-light.

### Two node types — document and tag
[ACTIVE]
The graph carries exactly two node types: documents (markdown files) and tags (free-form annotations). They're distinct dataclass types in the in-memory graph, not a schema discriminator on a unified node — Hoplite is schemaless, so there's no `kind` field. External resources (source code, URLs, binaries) are wrapped by a markdown document; never indexed directly. Resolves the deferred "source files as graph nodes" and "external web references" roadmap items.

### Sidecars hold machine-generated metadata only
[SUPERSEDED by: All derived state lives only in memory; no sidecars, no cache files]
Intermediate position: cache sidecars for machine-derived data (BM25, MinHash) while keeping authoritative metadata in frontmatter. Survived several turns; replaced by the fully-in-memory architecture when SQLite FTS5 made BM25 caching unnecessary and Mark accepted the MinHash cold-start cost.

### All derived state lives only in memory; no sidecars, no cache files
[ACTIVE]
The only persistence layer in the system is the corpus of `.md` files. Everything else — MinHash signatures, BM25 inverted indexes, edge adjacency, ghost nodes, the full in-memory graph — is derived at MCP startup from those files and held in RAM. No `.hoplite/cache.db`, no per-doc `.minhash.bin` sidecars, no persisted artifacts of any kind.

Runtime storage layout:

- `Graph.documents: dict[str, Document]`, `Graph.tags: dict[str, Tag]` — Python dicts (entities)
- `Graph.out_edges`, `in_edges`, `aliases` — Python dicts (adjacency + alias index)
- `Graph.fts: sqlite3.Connection` — in-memory `:memory:` SQLite with one FTS5 virtual table populated at startup; serves BM25 scoring
- `Graph.minhash: dict[str, bytes]` — per-doc 1024-byte signatures held in RAM (or stored as `bytes` on the `Document` dataclass — same outcome)

Cold-start budget at 1000 docs:

- Walk + body load: ~150ms (read ~5MB from SSD)
- FTS5 populate: ~500ms (C-backed tokenization)
- MinHash compute: ~50s — the dominant cost
- Pairwise MinHash for `:related`: ~100ms
- **Total: ~50s for 1000 docs, ~5s for 100 docs, ~5min for 5000 docs**

For a long-running MCP server (start once per session, run for hours), 50s startup is acceptable. The cost is decision-reversible — if the corpus ever grows past tolerable startup time, a persistent `.hoplite/cache.db` for MinHash can return without changing the rest of the architecture.

### BM25 via in-memory SQLite FTS5
[ACTIVE]
Text scoring runs through SQLite's FTS5 extension in an in-memory `:memory:` database. C-backed tokenization is faster than any pure-Python implementation; built-in BM25 scoring is sub-millisecond; corpus-level stats (IDF, avgdl, N) are maintained internally by FTS5.

`sqlite3` is in Python's stdlib — no new dependency, no persistent SQLite file (the `:memory:` database is rebuilt at every startup from the loaded bodies). Tag-expression filtering happens post-hoc on FTS5 results, using the in-memory edge adjacency.

This brings SQLite back as a runtime dep but only as a derived index — files remain the source of truth.

### Corpus-level statistics live only in memory
[ACTIVE]
Per-doc sidecars hold per-doc data — they can't carry stats that depend on the whole corpus. BM25 needs `N` (total doc count), `df(term)` (document frequency per term), and `avgdl` (average doc length). MinHash LSH (if/when adopted) needs the band-hash buckets. None of these is computable from one sidecar.

After the per-doc load pass, the walker runs an aggregate pass: accumulate `N`, `df(term)`, `avgdl`, and any LSH buckets in memory from the per-doc sketches. Nothing persisted. Query scoring waits until the aggregate pass completes.

No vault-level corpus sidecar (e.g., `.hoplite/corpus.json`) — that would reintroduce the cache-invalidation problem SQLite-out was supposed to retire. The aggregate pass is O(N) over loaded sidecars; sub-second at the thousands-to-tens-of-thousands scale.

MinHash LSH bucketing is deferred — pairwise scan over signatures is fine at current scale; LSH is the optimization to keep in mind if the `:related` derivation cost ever bites.

### MCP surface drops CRUD tools
[ACTIVE — surface list superseded by "All retrieval tools eliminated"]
With SQLite gone and files as source of truth, the write-side MCP tools (`insert_node`, `update_node`, `delete_node`, `index_node`, `apply_framing`) lose their reason to exist. Agents have Write, Edit, and Bash through Claude Code; they can write `.md` files directly. The `/hoplite` skill teaches the file shape, location convention, and wikilink rules — discipline lives in the protocol, not in tool signatures.

For the final surface (4 tools, not 6 — `invoke_node` and `read_node` die in the next entry), see "All retrieval tools eliminated; Hoplite is dataview over documents" below.

### Framing collapses to verb-driven binary
[SUPERSEDED by: All retrieval tools eliminated]
Brief intermediate position: kill `apply_framing`, retire per-tag framing, keep `invoke` (instruction envelope) and `read` (read envelope) as verb-driven framing. Lasted one turn.

### All retrieval tools eliminated; Hoplite is dataview over documents
[ACTIVE]
`hoplite_invoke_node` and `hoplite_read_node` both die. Hoplite stops being a content-retrieval system entirely. Agents discover candidates through `match_nodes` and `traverse_nodes` (which return paths, summaries, tags — no bodies), then use Claude's built-in `Read` tool to fetch file content.

This is the Dataview-over-the-vault model in its purest form. Hoplite is the query index; Read is the fetcher. The graph tells the agent what exists and what connects to what; the file tools handle content.

What dies with this:

- `hoplite_invoke_node`, `hoplite_read_node`
- Both envelope files (`instruction.md`, `read.md`)
- `Envelope` and `FetchedNode` types in the data model
- Envelope composition section in `behavior.md`
- `.hoplite/envelopes/` directory
- "Verb is the intent" section in the `/hoplite` skill
- All framing-axis concepts; the tag names `instruction` / `reference` / `observation` lose any special status

Final MCP surface (4 tools):

1. `hoplite_match_nodes(predicate, k)` — BM25 + tag-expression filter; returns `(path, summary, tags, score)` records
2. `hoplite_traverse_nodes(from, depth, predicate)` — graph walk; returns `(path, summary, tags, distance, via_edges)` records
3. `hoplite_reindex()` — optional explicit rescan; otherwise auto-detects via stat+content_hash on next query
4. `hoplite_dump_index(path?)` — debug snapshot. Snapshots the in-memory state to a SQLite file. Default destination `.hoplite/index.sqlite` (hidden directory convention, alongside `.git/` and `.obsidian/`). Optional `path` parameter for custom destinations.

   - One-shot operation — the file is overwritten each call. No live mirroring.
   - Returns the absolute path of the written file plus row counts as a `WriteResult`.
   - Schema mirrors the in-memory shape (documents, document_tags, document_aliases, tags, edges, plus an FTS5 mirror). See "hoplite_dump_index schema" entry below for the full DDL.
   - Then `sqlite3 .hoplite/index.sqlite` gives developers a full SQL surface over the derived state.

### Edge vocabulary — closed set of three
[ACTIVE]
Three edge kinds, closed set. No aspirational types reserved for future passes.

- **`member`** (tag→doc) — internal storage name. External query surface reads as `tagged` (predicate sugar that translates to traversal over `member` edges with src filtered to a tag). Internal vocabulary matches the container structure (`Tag.members`); external vocabulary matches user mental model from Obsidian.
- **`mentions`** (doc→doc) — extracted from `[[wiki-link]]` references in body text. Emitted at startup walk.
- **`related`** (doc↔doc, symmetric) — emitted by MinHash similarity pass at startup over the cached signatures. Above-threshold pairs become bidirectional `related` edges.

Aspirational types previously reserved in `roadmap.md` (`cites`, `contradicts`, `requires`, `see-also`, `parent`, `supersedes`) are dropped. Their use cases collapse into the three above:

- `cites`, `requires`, `see-also` — `mentions` with the qualifier expressed in prose
- `contradicts` — `mentions` plus body text expressing the contradiction
- `parent` — was for label hierarchy; moot with schemaless tags
- `supersedes` — frontmatter property or prose-level

The richer semantics live in prose, frontmatter, or implicit via traversal patterns. Matches Obsidian's model: one edge type (the wikilink) plus everything else inferred.

### `slugify_text` tool eliminated
[ACTIVE]
The tool was load-bearing when filenames and tag IDs had to be canonical kebab-case enforced by the server — agents called `slugify_text` to normalize human input before submitting. With files-as-source-of-truth, paths are agent-chosen presentation (no canonical-ID role), and tag canonicality is taught by the `/hoplite` skill rather than enforced by tool boundary. The function has no use case as an MCP surface tool.

Internal `slugify` helper may or may not survive depending on whether the walker or any analysis pass needs to canonicalize a string. If kept, it lives in a private module; not on the MCP surface.

### Drop SQLite; in-memory graph; files-as-source-of-truth
[ACTIVE — refined]
Dataview-style architecture. Scan corpus at startup, build in-memory graph from frontmatter and bodies, files are the only persistence. At Hoplite's expected scale (hundreds to low thousands of documents), SQLite as persistent storage is unnecessary overhead.

Refinement: SQLite later came back as an *in-memory derived index* for BM25 text scoring via FTS5 — see "BM25 via in-memory SQLite FTS5" above. The `:memory:` database is rebuilt at every startup; no persistent SQLite file. The "files as source of truth" principle holds — SQLite's role narrowed from storage substrate to disposable runtime index.

### Identity collapses to single tier (path)
[ACTIVE]
Without SQLite there is no persistence-layer ID to keep stable across renames. Path is the only identifier. Dict keys in the in-memory graph are path strings. Aliases handle rename continuity.

### Labels and tags un-collapsed; both are container categories
[SUPERSEDED by: Schemaless — only tags, no labels]
Imported Neo4j's label-as-schema concept. Hoplite is schemaless and that vocabulary doesn't apply.

### Schemaless — only tags, no labels
[ACTIVE]
Hoplite has no schema. Neo4j-style labels (closed-vocabulary type discriminators) don't exist. The only categorization mechanism is tags — open-vocabulary, user-authored annotations.

The model:

- **Documents** — markdown files, identified by path, with frontmatter and body.
- **Tags** — free-form annotations, first-class graph nodes that contain members.
- **Edges** — typed relations: `member` (tag→doc), `mentions` (doc→doc), `related` (doc↔doc).

Documents and tags are different *structural shapes* in the in-memory graph — different dataclass types, different containers (`Graph.documents`, `Graph.tags`) — but neither carries a schema label. The distinction is implicit in the type system, not declared via a discriminator field. If you want "all documents," you iterate `Graph.documents`; if you want "all tags," you iterate `Graph.tags`. No query verb needed.

The query surface for membership is just `tagged: X` (open-vocabulary tag membership via `member` edge traversal). No `kind:` predicate because there's no kind concept to filter on.

### Wikilink forward references — accept and materialize a ghost node
[ACTIVE]
A wikilink to a path that doesn't yet exist resolves to a **ghost node** — a first-class graph entity with the canonical identity (slug) but no body content. Real-to-ghost edges sit in the graph alongside real-to-real edges; no side tables, no "pending references" queue. When a document with the matching identity is later added, the ghost is **promoted** in place: identity stays stable, content fields fill in, every inbound edge already points to the right place because the node ID never changed.

Why ghost-as-first-class:

- Same trick git uses (content-addressed hash, resource may or may not exist locally), the same trick the web uses (URL is identity, target may 404), the same trick Smalltalk's `become:` uses. Identity is decoupled from existence.
- Makes "open loops" queryable for free — `unresolved_targets()` returns the ghost set, which is exactly the user's intent backlog of documents they've referenced but not yet written.

Dataclass shape: single `Document` type with a `resolved: bool` flag. Ghost docs have `body=None, title=None, summary=None, content_hash=None`. One dict in the graph; queries filter by `resolved` when needed.

Edge metadata: every Edge carries `(source_path, line, column)` so dangling links can be located and re-parsed. Cost: ~40 extra bytes per edge, ~400KB at 1000-doc scale.

Walker is **two-pass logically** (three concerns, two file walks):

1. **Identity collection** — scan filenames + frontmatter aliases → build `alias_or_path → canonical_path` index. Cheap (just frontmatter).
2. **Body load + wikilink parsing + edge materialization** — loads bodies, parses wikilinks against the identity index, creates ghosts on misses, accumulates BM25 sketches, refreshes sidecars. Followed by the in-memory aggregate pass for corpus stats and `:related` pairwise.

Two-pass is required (not just nice) — single-pass gets alias resolution wrong when a referrer is processed before the referent's aliases are known.

### `hoplite_dump_index` schema
[ACTIVE]
The one-shot snapshot at `.hoplite/index.sqlite` mirrors the in-memory shape so developers can run SQL against the derived state.

```sql
CREATE TABLE documents (
  path TEXT PRIMARY KEY,
  resolved INTEGER NOT NULL,
  title TEXT,
  summary TEXT,
  body TEXT,
  content_hash TEXT,
  created_at REAL,
  updated_at REAL,
  minhash BLOB
);

CREATE TABLE document_tags (
  path TEXT NOT NULL,
  tag TEXT NOT NULL,
  PRIMARY KEY (path, tag)
);

CREATE TABLE document_aliases (
  path TEXT NOT NULL,
  alias TEXT NOT NULL,
  PRIMARY KEY (path, alias)
);

CREATE TABLE tags (
  slug TEXT PRIMARY KEY,
  text TEXT NOT NULL,
  summary TEXT
);

CREATE TABLE edges (
  src TEXT NOT NULL,
  dst TEXT NOT NULL,
  kind TEXT NOT NULL,
  confidence REAL,
  source TEXT,
  rationale TEXT,
  source_path TEXT,
  line INTEGER,
  "column" INTEGER,
  PRIMARY KEY (src, dst, kind)
);

CREATE VIRTUAL TABLE fts USING fts5(path, title, summary, body);
```

Notes:

- `documents.resolved` is the ghost-vs-real flag from the wikilink-forward-references decision; ghost docs have `resolved = 0` and `title`, `summary`, `body`, `content_hash`, `created_at`, `updated_at`, `minhash` all NULL.
- `column` is quoted because it's a SQLite reserved word.
- The `fts` virtual table is the same shape as the production in-memory FTS5 mirror — lets developers reproduce match scoring with `SELECT path, bm25(fts) FROM fts WHERE fts MATCH ? ORDER BY rank`.
- Edge `confidence`, `source`, `rationale` are nullable — only `:related` edges populate them; authored `:mentions` and `:member` edges leave them NULL.
- `source_path`, `line`, `column` are populated for `:mentions` edges (where the wikilink lives in the source); NULL for derived edges.

### Auto-reindex trigger — day-one explicit, aspirational per-query stat
[ACTIVE]
Day one: no automatic detection of file changes between queries. Agents call `hoplite_reindex()` after they've written files; humans editing the corpus in Obsidian see their changes after the next reindex call.

Aspirational upgrade: per-query stat-check. Every `match_nodes` / `traverse_nodes` walks the corpus and stat()s every file; mtime or content_hash mismatch triggers refresh of the affected doc. Cost is ~5ms per 1000 files per query — small. Pulls hand-edits in transparently.

The `watchdog` file-watcher option (background thread, instant detection) is the most agile but adds a dependency. Deferred indefinitely; only worth it at scales where per-query stat starts to bite.

### Wikilink and tag lookup — case-insensitive ordinal
[ACTIVE]
Internal lookups (wikilink resolution, alias lookup, tag matching) are case-insensitive ordinal — Python `str.casefold()`, equivalent to C# `StringComparison.OrdinalIgnoreCase`. Locale-independent, byte-level.

The graph stores paths and tag slugs in their authored casing (filesystem case for paths, frontmatter case for tags). A parallel case-folded → canonical-key index alongside `Graph.documents` and `Graph.tags` gives O(1) case-insensitive lookup at small memory cost (~50KB for 1000 paths).

`[[Notes/Foo.MD]]`, `[[notes/foo.md]]`, and `[[NOTES/foo.MD]]` all resolve to the same canonical doc. `tagged: GraphDB` matches `tagged: graphdb`. Results returned by `match_nodes` and `traverse_nodes` carry canonical casing so agents who pass paths to Claude's `Read` tool get the filesystem-correct form.

### Tag auto-derive — none; agent supplies
[ACTIVE]
No system-driven auto-derive from path, filename, or content. Agents supply tags explicitly in frontmatter. The earlier auto-derive rules (leading path segment as a tag, ISO date prefix as a tag) presupposed that filenames were canonical IDs with a slug grammar — now that paths are arbitrary agent-chosen presentation, those rules don't apply.

Roadmap candidate: optional Sonnet-driven enrichment as an opt-in flag on `hoplite_reindex(enrich_tags=True)`. The server spawns a sub-agent that reads document bodies and suggests tag additions. Deferred — agent supplies remains the default, enrichment is a future feature.

### Frontmatter mandatory fields: `title`, `summary`, `tags`, `created`, `aliases`
[ACTIVE]
`title` and `summary` lifted from the body-shape contract. `tags` replaces `labels` (list of slugs; can be empty). `created` is new — every document carries a creation date in ISO format. `aliases` is a list; defaults to empty.

### Frontmatter allows user-defined properties
[ACTIVE]
Beyond the system-defined fields, arbitrary YAML keys pass through. Example: `status: draft`. The system reads and stores user-defined keys but doesn't act on them. Available for user queries and external tools (Obsidian, Dataview).

Example frontmatter:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, notes]
created: 2026-05-24
aliases: [pgraph, labeled property graph]
status: draft
---
```

### `updated` derives from git history, not frontmatter or mtime
[ACTIVE]
Git is the source of truth for modification time. The server reads commit history when it needs the value (untracked files have no `updated`). Not a queryable an agent or normal user would reach for; deemphasized in tool API and skill protocol.

### Tables in spec docs: stop adding, leave existing
[ACTIVE]
The writing-prose rules avoid tables outside worked examples. Going forward, no new tables in spec docs. Existing tables stay — no retroactive edits to remove them.

### Hoplite is Obsidian for agents
[ACTIVE]
The positioning frame. Obsidian's vault model — markdown files with YAML frontmatter, wikilinks, tags, aliases — is the substrate. Hoplite layers an MCP-callable graph API on top so agents can read, write, traverse, and query the vault the way humans do through Obsidian. Hand-edits round-trip; users can open the corpus in Obsidian directly. Every design decision should preserve Obsidian-compatibility — frontmatter field names, wikilink syntax, file layout — so the vault stays portable to and from Obsidian without conversion.

### Edge reification deferred — edges aren't first-class nodes
[ACTIVE]
Mathematically, a directed multigraph is symmetric: edges are nodes-with-arity-2-incidence (the bipartite incidence encoding makes this rigorous; line graph and subdivision functors operationalize it). In principle Hoplite could reify edges as nodes — letting one edge be the source or target of another, supporting "Alice contradicted Bob's claim about X" as an edge-on-edge.

Day one doesn't do this. Edges live in `Graph.out_edges` / `Graph.in_edges` as their own structural type, distinct from nodes. The existing edge attributes (`confidence`, `source`, `rationale`, `source_path`, `line`, `column`) cover provenance, weight, and source position without needing reification.

If reification ever becomes a requirement, the schema grows toward it (an edge gets a path-like identity; `src` / `dst` can point to edges; the in-memory model adds an `edges` dict keyed by edge identity). Alternative: migrate to a hypergraph backend like HypergraphDB or AtomSpace, which take the symmetric view natively.

Flagging as a known design seam so the choice is conscious rather than rediscovered.

### Proxy-documents for external content confirmed as Obsidian-native
[ACTIVE]
Wrapping external content (source code, URLs, PDFs, transcripts, binaries) in a markdown document is a normal Obsidian workflow, not a Hoplite invention. The proxy document summarizes the source, carries its location (path, URL, or other reference), and participates in the graph like any other document. This validates the earlier "two node kinds only" decision — the external-content question never reaches the graph schema.
