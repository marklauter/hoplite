# Implementation alternatives

[Implementation, overlay] Operational extensions that apply on top of either implementation A ([file-based](implementation-file-based.md)) or implementation B ([SQLite-hybrid](implementation-sqlite-hybrid.md)). Contracts in [data-model.md](data-model.md), [tool-api.md](tool-api.md), [behavior.md](behavior.md), and [orchestrator-skill.md](orchestrator-skill.md) stay unchanged across all of these.

The SQLite-hybrid implementation moved out of this file into [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md) as a peer to the file-based implementation. The two implementations are alternatives; the overlays below apply to whichever one is chosen.

## Write-ahead journal for cross-file atomicity (file-based only)

The [file-based implementation](implementation-file-based.md#atomicity) is best-effort across files — per-file writes use temp-and-rename, but a crash mid-sequence leaves the index briefly inconsistent.

A write-ahead journal lifts the guarantee to genuine cross-file transactional semantics:

- Before any file change, append a journal record describing all intended file operations for this write.
- Perform the operations.
- On clean completion, remove the journal record.
- On startup, replay any non-empty journal records — finishing partial writes or rolling them back.

Combined with file locking on the per-node write path (see below), this closes the half-written-graph window without abandoning the filesystem-as-storage shape.

If the SQLite-hybrid implementation is chosen instead, this concern dissolves into SQLite's native ACID — no journal-on-files needed. The overlay applies only when the chosen implementation is file-based.

## Multi-writer support

Day one assumes a single writer. Multi-agent is the actual target. The story differs by chosen implementation:

Under the file-based implementation: add file locking on the per-node write path — the authored note file plus the node's sidecar. Simultaneous writes to the same node serialize. The folder-per-label membership shape already removes the popular-label contention concern. Combine with the write-ahead journal above for cross-file atomicity across the per-node + per-label operation sequence.

Under the SQLite-hybrid implementation: multi-writer collapses to SQLite's connection model with WAL mode. The database serializes writers natively; the only remaining concern is the per-node authored file write, which still needs per-id file locking. The journal-on-files mechanism is unneeded — SQLite's transactional commit covers what the journal was for.

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
