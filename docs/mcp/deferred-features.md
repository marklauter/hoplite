# Deferred features

[Roadmap] Features designed but not in day one. Each is a data-model or operational extension that lands when the use case justifies the build. Contracts in [data-model.md](data-model.md), [tool-api.md](tool-api.md), [behavior.md](behavior.md), and [orchestrator-skill.md](orchestrator-skill.md) stay unchanged for all of these.

## Multi-writer support

Day one assumes a single writer. Multi-agent is the actual target.

SQLite in WAL mode supports one writer plus many concurrent readers without blocking; the database serializes writers natively. The MCP server accepts concurrent write calls and lets SQLite queue them — no application-level locking needed for the relational layer.

The remaining concern is the per-node authored file write: two writers updating the same `<corpus_root>/docs/<id>` race on the file. The SQLite transaction can still commit cleanly for whichever wins, but the file may not match what the last-committed transaction expected. Multi-writer support adds per-id file locking on the authored note path, paired with SQLite's native transaction serialization.

## Source files as graph nodes

The current spec implicitly scopes the corpus to markdown notes under `<corpus_root>/docs/`. The graph model itself is type-agnostic; indexing source code files as nodes is a natural extension.

See `[[source-files-as-graph-nodes]]` for the full analysis. Summary of what changes when code joins:

- "Authored note" generalizes to "authored content." The H1/blank/summary/blank/body shape is markdown-only. Source files derive summary from docstring, first comment block, or filename. Body validation becomes file-type-conditional.
- Wiki-link parsing for `:mentions` is markdown-only. Code has its own reference graph — imports, definitions, references, inheritance — derivable from AST or LSP. These join the authored-edge category.
- The auto-derived path-segment label generalizes naturally: a source file at `src/foo/bar.py` carries `src` as the first-segment label (or the indexer can adopt a different rule for non-content paths). Sub-labels for language (`python`, `csharp`, `typescript`) join from filename extension.
- `insert`/`update`/`delete` are markdown-only. Source files get indexed via `index(id)` but written through normal coding workflows (IDE, Claude Code's Edit tool), not the MCP write surface. Closer to LSP's read-mostly model for code.
- A fourth framing-axis label (candidate name `definition` — "you are reading the canonical source of behavior") joins the `instruction`/`reference`/`observation` trio when code lands.

Cross-boundary traversal (notes ↔ code) is the agentic value-add: "show me notes that mention this function" and "show me code paths the discussion in this note refers to."

The spec is forward-compatible because the structural moves (label inverted index, structured envelope, typed edges, source-of-truth split) don't assume markdown.

## External web references as first-class nodes

The current spec wraps external sources in local reference notes — a note summarizes the source and carries the URL in its body. A future pass could promote external sources to first-class nodes with their own labels and edges (a `web` or `external` label, edges between cited URLs and citing notes, possibly periodic re-fetch to detect updates).

The wrapping pattern works today and defers the question. The graph still tracks external references; they just travel through a local note rather than appearing as their own nodes.

## Reindex trigger model

When the server-side reindex pass lands (MinHash, embeddings — see [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md#reindex--deferred-not-forgotten)), it needs a trigger model. Options:

- Manual CLI — operator runs `reindex` when they want it.
- Scheduled — cron-style periodic invocation.
- File-watcher — detects changes under `<corpus_root>/docs/` and triggers automatically.
- Write-trigger-drain — `insert`/`update`/`delete` enqueue work for a background drain process.

Each has different operational shape and failure modes. Decided when reindex itself is built.
