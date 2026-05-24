# Roadmap

Features designed and named but not in day one. Each lands when the use case justifies the build. Contracts in [data-model.md](data-model.md), [tool-api.md](tool-api.md), [behavior.md](behavior.md), and [orchestrator-skill.md](orchestrator-skill.md) hold unchanged for all of these — the schema columns that store deferred data (`embedding_path`, `confidence`, `source`, `in_edges`) are already present in the day-one shape, ready for population when the feature lands.

## Server-side reindex pass

Day one has no server-side reindex. The agent-as-driver pattern handles "soft reindex" through `index(id)` calls — walk the corpus, call `index` on each file, the write-time flow re-derives metadata. That covers stale rows, hand-edited bodies, and missing cached fields.

The features that genuinely need server-side compute live here:

- MinHash pairwise relatedness — Jaccard-similarity edges above `minhash_threshold` (0.20 default) materialize as `:related` derived edges with `source: minhash`. Adds rows to `edges` in batches across one transaction.
- Embedding generation via local Ollama (`nomic-embed-text` candidate, 768-dim, ~270MB, CPU-fast) writes `.npy` files into `<corpus_root>/.graph/embeddings/` and populates `nodes.embedding_path`. With embeddings, `match` switches from BM25 to vector similarity, and embedding-derived `:related` edges supplement MinHash.

A bulk reindex pass is fast under SQLite: one transaction can insert thousands of `:related` edges in a single commit.

### Trigger model

When the reindex pass lands, it needs a trigger model. Options:

- Manual CLI — operator runs `reindex` when they want it.
- Scheduled — cron-style periodic invocation.
- File-watcher — detects changes under `<corpus_root>/docs/` and triggers automatically.
- Write-trigger-drain — `insert`/`update`/`index`/`delete` enqueue work for a background drain process.

Each has different operational shape and failure modes. Decided when reindex itself is built.

## Multi-writer support

Day one assumes a single writer. Multi-agent is the actual target.

SQLite in WAL mode supports one writer plus many concurrent readers without blocking; the database serializes writers natively. The MCP server accepts concurrent write calls and lets SQLite queue them — no application-level locking needed for the relational layer.

The remaining concern is the per-node authored file write: two writers updating the same `<corpus_root>/docs/<id>` race on the file. The SQLite transaction can still commit cleanly for whichever wins, but the file may not match what the last-committed transaction expected. Multi-writer support adds per-id file locking on the authored note path, paired with SQLite's native transaction serialization.

## Pagination for `match` and `traverse`

Day one, `match` returns up to `k` landings in one shot; `traverse` returns every node reachable within `depth` layers. Both are bounded but neither paginates.

Pagination becomes useful when corpus growth makes `k` increasingly limiting (the agent wants the top 5 but knows there are 50 worth examining if needed), or when traversal at depth ≥ 2 across hub nodes returns hundreds of results that the agent wants to walk incrementally.

Likely shape — cursor-based, following MCP convention:

- `match(predicate, k=5, cursor=null)` returns `{landings: [...], nextCursor?: string}`. Passing the cursor back continues from where the prior response left off.
- `traverse(from, depth=1, predicate, cursor=null)` follows the same pattern.

Cursors encode the query state (predicate, position, deterministic sort order) opaquely. The agent treats them as opaque strings. Specifics decided when corpus scale makes the day-one limit felt.

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

## Aspirational edge types

Day-one edge vocabulary is `mentions` (authored, from wiki-links) and `related` (derived or authored). Additional types are reserved for future passes when corpus patterns repeatedly call for them:

- `cites` — source explicitly cites target as backing.
- `contradicts` — source opposes target's claim.
- `requires` — source depends on target (skill composition).
- `see-also` — topical adjacency the author wants to surface explicitly, independent of derived similarity.
- `blocked-by` — work that can't proceed without resolution of the target.
- `parent` — hierarchy among labels.
- `supersedes` — source replaces target.

Adding a new type is cheap once a pattern recurs: pick a name, document the semantic, teach the indexer to emit it (if it should auto-emit from some source), update the orchestrator skill's vocabulary section.

## Migration of legacy corpus

The legacy `docs/notes/` corpus (with YAML frontmatter on notes from the pre-graph era) needs migration to the new shape. A converter walks every note, derives labels from filenames and existing frontmatter, populates the database, and writes the bootstrapped envelope files into `<corpus_root>/.graph/`. Day-one development can use a fresh empty corpus or a hand-curated subset; full migration runs as a one-time CLI pass when it lands.
