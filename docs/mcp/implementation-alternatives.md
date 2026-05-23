# Implementation alternatives

[Implementation, future] Storage and operational variants that swap or extend the day-one file-based design. Contracts in [data-model.md](data-model.md), [tool-api.md](tool-api.md), [behavior.md](behavior.md), and [orchestrator-skill.md](orchestrator-skill.md) stay unchanged across all of these.

## SQLite for the relational layer

The day-one folder-per-label scheme is a degenerate key-value store: folder is the table, filename is the key, empty file is value-by-presence. Same semantics as `PutItem` with no attributes. SQLite gives the same semantics in one file with real query capability.

The hybrid: SQLite for the relational layer, files for the prose layer.

```
Files (content + prose):
  docs/notes/<id>.md                authored notes (unchanged)
  docs/index/labels/<label>.md      label envelopes (unchanged)
  docs/index/envelopes/read.md      read content envelope (unchanged)
  docs/index/embeddings/<id>.npy    embedding blobs (unchanged)

SQLite (everything relational):
  docs/index/graph.db               single file holding:
    - nodes (id, summary)
    - labels (id, summary, has_envelope)
    - label_membership (label, member_id)
    - edges (source_id, type, target_id, confidence, source, rationale)
```

What collapses from [implementation-file-based.md](implementation-file-based.md):

- Per-node `.yml` sidecars become rows in `nodes` plus their owned `edges`.
- Per-label `.yml` sidecars become rows in `labels`.
- Membership marker files become rows in `label_membership`.

What stays unchanged:

- Tool API surface — identical signatures, identical semantics.
- Envelope composition — framing + primes from label envelopes' `.md` prose.
- Notes stay as files. Label envelope prose stays as files. Embedding blobs stay as files.
- Source-of-truth split — notes for body content, label envelope files for prose. Relational state in SQLite becomes the new source of truth for memberships and edges; the database's ACID guarantees replace the day-one repair-on-read story.

What it buys:

- Composite queries — "all nodes labeled X AND not labeled Y" is one SQL statement instead of N filesystem reads.
- Bidirectional indexes — "which labels does node X carry" and "which nodes carry label X" are both fast queries against indexed columns.
- Edge graph proper — `out_edges` and cached `in_edges` become two views of one source of truth. The "symmetric `:related` edges written on both sides" trick goes away — store once, query either direction.
- Bulk writes — a reindex pass touching 1000 membership entries is one transaction instead of 1000 filesystem operations.
- ACID writes — no more best-effort cross-file atomicity; the database handles it.

What it costs:

- `ls docs/index/labels/skills/` no longer enumerates members. Membership queries go through the MCP API (which is the use case anyway — agents call `traverse`/`match`, not `ls`).
- Per-membership git diff goes away. But membership churn isn't typically interesting in commits; content changes are.
- Hand-editing memberships becomes API-only. For an agentic system this is right.

Plugin packaging: Python's stdlib has `sqlite3` — no dependency to add. The `.db` file is created on first run via a schema migration in startup code; gitignored.

Triggers for moving to this implementation: popular-label contention surfaces, transactional needs across multiple entities become load-bearing, or `:related` edge reindex passes need batch performance the filesystem can't deliver.

## Write-ahead journal for cross-file atomicity

Day-one [implementation-file-based.md](implementation-file-based.md#atomicity) is best-effort across files — per-file writes use temp-and-rename, but a crash mid-sequence leaves the index briefly inconsistent.

A write-ahead journal lifts the guarantee to genuine cross-file transactional semantics:

- Before any file change, append a journal record describing all intended file operations for this write.
- Perform the operations.
- On clean completion, remove the journal record.
- On startup, replay any non-empty journal records — finishing partial writes or rolling them back.

Combined with file locking on the per-node write path (see below), this closes the half-written-graph window without abandoning the filesystem-as-storage shape. Specifics are designed when the day-one shape's limits become visible.

If the SQLite-for-relational alternative lands first, this concern dissolves into SQLite's native ACID — no journal-on-files needed.

## Multi-writer support

Day one assumes a single writer. Multi-agent is the actual target. Multi-writer support adds:

- File locking on the per-node write path — `docs/notes/<id>.md` and `docs/index/<id>.yml`. Simultaneous writes to the same node serialize.
- The write-ahead journal above for cross-file atomicity across the per-node + per-label operation sequence.

The folder-per-label membership shape already removes what would have been the worst contention point. Two writers updating different members of the same popular label never collide — they create different filenames.

Under the SQLite alternative, multi-writer collapses to SQLite's connection model with WAL mode. The per-node locking and journal needs go away.

## Source files as graph nodes

The current spec implicitly scopes the corpus to markdown notes under `docs/notes/`. The graph model itself is type-agnostic; indexing source code files as nodes is a natural extension.

See `[[source-files-as-graph-nodes]]` for the full analysis. Summary of what changes when code joins:

- "Authored note" generalizes to "authored content." The H1/blank/summary/blank/body shape is markdown-only. Source files derive summary from docstring, first comment block, or filename. Body validation becomes file-type-conditional.
- Wiki-link parsing for `:mentions` is markdown-only. Code has its own reference graph — imports, definitions, references, inheritance — derivable from AST or LSP. These join the authored-edge category.
- `note` as the lone auto-derived label is too narrow. Becomes `note` for `docs/notes/`, `code` for source dirs, with sub-labels for language (`python`, `csharp`, `typescript`).
- `insert`/`update`/`delete` are markdown-only. Source files get indexed but written through normal coding workflows (IDE, Claude Code's Edit tool), not the MCP write surface. Closer to LSP's read-mostly model for code.
- A fourth framing-axis label (candidate name `definition` — "you are reading the canonical source of behavior") joins the `instruction`/`reference`/`observation` trio when code lands.

Cross-boundary traversal (notes ↔ code) is the agentic value-add: "show me notes that mention this function" and "show me code paths the discussion in this note refers to."

The spec is forward-compatible because the structural moves (folder-per-label, type-agnostic sidecar, structured envelope, typed edges, source-of-truth split) don't assume markdown.

## Other future directions

- Embeddings via Ollama — already documented in [implementation-file-based.md](implementation-file-based.md#reindex--deferred-not-forgotten) as the day-two reindex scope. Doesn't change storage substrate; adds `.npy` files and an embedding-based search path.
- External web references as their own node type — the current spec wraps external sources in local reference notes (a note summarizes the source and carries the URL in its body). A future pass could promote external sources to first-class nodes with their own labels and edges. Today's wrapping pattern works and defers the question.
- Reindex trigger model — manual CLI, scheduled, file-watch, or write-trigger-drain. Decided when reindex itself is built.
