# Roadmap

Features designed and named but not in day one. Each lands when the use case justifies the build. Contracts in [data-model.md](data-model.md), [tool-api.md](tool-api.md), [behavior.md](behavior.md), and [hoplite-skill.md](hoplite-skill.md) hold unchanged for all of these — the schema columns that store deferred data (`embedding_path`, `confidence`, `source`, `in_edges`) are already present in the day-one shape, ready for population when the feature lands. MinHash and derived `:related` edges, originally listed here, moved to day one and now live in the write-time flow in [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md#minhash-details).

## Server-side reindex pass — embeddings

Day one has no batch server-side reindex. MinHash signatures and derived `:related` edges materialize on every write through the normal write flow (see [implementation-sqlite-hybrid.md](implementation-sqlite-hybrid.md#minhash-details)). The agent-as-driver pattern via `hoplite_index_node(id)` covers stale rows, hand-edited bodies, and missing cached fields.

The one feature that still wants server-side compute: embedding generation via local Ollama (`nomic-embed-text` candidate, 768-dim, ~270MB, CPU-fast). The reindex pass writes `.npy` files into `<corpus_root>/.hoplite/embeddings/` and populates `nodes.embedding_path`. With embeddings, `hoplite_match_nodes` switches from BM25 to vector similarity, and embedding-derived `:related` edges supplement MinHash.

A bulk embedding pass is fast under SQLite: one transaction can update thousands of rows in a single commit. Whether embeddings need to recompute every write (like MinHash) or stay batch-deferred depends on Ollama's call-time cost in practice — MinHash takes milliseconds; an embedding model call may take 50-500ms per node and is a heavier write-path budget.

### Trigger model

When the embeddings pass lands, it needs a trigger model. Options:

- Manual CLI — operator runs `reindex` when they want it.
- Scheduled — cron-style periodic invocation.
- File-watcher — detects changes under `<corpus_root>/docs/` and triggers automatically.
- Write-trigger-drain — `hoplite_insert_node`/`hoplite_update_node`/`hoplite_index_node`/`hoplite_delete_node` enqueue work for a background drain process.
- Synchronous on write — same shape as MinHash, accepting the embedding-call latency.

Each has different operational shape and failure modes. Decided when the embedding pass itself is built.

## Multi-writer support

Day one assumes a single writer. Multi-agent is the actual target.

SQLite in WAL mode supports one writer plus many concurrent readers without blocking; the database serializes writers natively. The MCP server accepts concurrent write calls and lets SQLite queue them — no application-level locking needed for the relational layer.

The remaining concern is the per-node authored file write: two writers updating the same `<corpus_root>/docs/<id>` race on the file. The SQLite transaction can still commit cleanly for whichever wins, but the file may not match what the last-committed transaction expected. Multi-writer support adds per-id file locking on the authored note path, paired with SQLite's native transaction serialization.

## Open question — collapse match and traverse into a unified query DSL?

Day one has two discovery tools: `hoplite_match_nodes` (BM25 similarity over the whole corpus, no notion of starting node) and `hoplite_traverse_nodes` (BFS walk from a known node, no notion of ranking). Each has a clear use case the agent picks between.

A richer query language — Cypher-style `MATCH ... WHERE ... RETURN` — could collapse both into one tool. The expressive power would let queries combine ranking and traversal in one shot ("find nodes similar to this phrase that are also reachable from origin within 2 hops, ranked by relevance"), which today requires two-call composition by the agent.

What you'd gain:

- One discovery surface instead of two.
- Combined queries — BM25 plus graph constraints plus label filtering in one expression — that today are awkward or impossible without multiple round trips.
- Closer to a "real" graph query language; Cypher fluency carries over.

What you'd lose:

- The agent has to know enough of the DSL to compose valid queries. Two simple tools with one-line descriptions are easier to pick from than one expressive query language.
- Implementation complexity. A SQL-backed query planner that handles ranking + traversal + label filtering is a larger build than the two simple flows day one.
- The label expression added to predicates day one already covers most of the gap — `hoplite_match_nodes` with `node_labels` answers "find me notes about caching tagged architecture" without needing a DSL.

A middle option: keep `hoplite_match_nodes` and `hoplite_traverse_nodes` as the simple primitives, add a third tool `hoplite_query` that takes a Cypher-ish expression for the cases that need combined ranking + traversal. Easy cases stay easy; expressive queries get their own tool.

Open question — pending a corpus or agentic use case that recurrently wants combined queries. Until then, the two-tool surface with label expressions is the design.

## Open question — does pagination ever land?

Day one, neither discovery tool paginates. `hoplite_match_nodes` returns the top `k` results in one shot; `hoplite_traverse_nodes` returns whatever's bounded by `depth` and the predicate. The MCP best-practices reference recommends pagination from day one (limit + has_more + next_offset metadata); we deliberately diverge because the natural caps are sufficient for the expected use cases and pagination on graph data is structurally awkward.

What you'd gain by adding pagination:

- The agent can ask for the top 5 from a relevance ranking but page through to 50 if needed, without recomputing.
- Large traversal results from hub nodes become walkable incrementally instead of all-or-nothing.
- Closer alignment with the MCP best-practices reference.

What you'd lose:

- `hoplite_match_nodes` becomes more complex than the simple "top-k" the agent picks `k` for. The k cap is doing real work as a self-limiting design.
- `hoplite_traverse_nodes` pagination requires either caching the full BFS walk (memory cost) or encoding BFS state — visited set, frontier queue — in a continuation token (large, awkward). Neither is appealing.

Two possible shapes if it lands:

- Continuation-token pagination — `hoplite_match_nodes(predicate, k=5, continuation_token=null)` returns `[Landing]` plus an optional `next_continuation_token` when more results are available. Token opaquely encodes query state (predicate, last score+id seen, sort order). Robust to concurrent inserts; clean for the sorted-score result set match returns.
- Pagination on match only, never on traverse — match's results are a sorted list, well-suited to continuation tokens. Traverse pagination may never make sense; bound by `depth` and tighten the predicate instead.

Open question — pending a corpus or agentic use case that recurrently bumps into the day-one caps. Until then, the no-pagination surface plus the `k` and `depth` caps is the design.


## Source files as graph nodes

The current spec implicitly scopes the corpus to markdown notes under `<corpus_root>/docs/`. The graph model itself is type-agnostic; indexing source code files as nodes is a natural extension.

See `[[source-files-as-graph-nodes]]` for the full analysis. Summary of what changes when code joins:

- "Authored note" generalizes to "authored content." The H1/blank/summary/blank/body shape is markdown-only. Source files derive summary from docstring, first comment block, or filename. Body validation becomes file-type-conditional.
- Wiki-link parsing for `:mentions` is markdown-only. Code has its own reference graph — imports, definitions, references, inheritance — derivable from AST or LSP. These join the authored-edge category.
- The auto-derived path-segment label generalizes naturally: a source file at `src/foo/bar.py` carries `src` as the first-segment label (or the indexer can adopt a different rule for non-content paths). Sub-labels for language (`python`, `csharp`, `typescript`) join from filename extension.
- `hoplite_insert_node`/`hoplite_update_node`/`hoplite_delete_node` are markdown-only. Source files get indexed via `hoplite_index_node(id)` but written through normal coding workflows (IDE, Claude Code's Edit tool), not the MCP write surface. Closer to LSP's read-mostly model for code.
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

Adding a new type is cheap once a pattern recurs: pick a name, document the semantic, teach the indexer to emit it (if it should auto-emit from some source), update the `/hoplite` skill's vocabulary section.

## Migration of legacy corpus

The legacy `docs/notes/` corpus (with YAML frontmatter on notes from the pre-graph era) needs migration to the new shape. A converter walks every note, derives labels from filenames and existing frontmatter, populates the database, and writes the bootstrapped envelope files into `<corpus_root>/.hoplite/`. Day-one development can use a fresh empty corpus or a hand-curated subset; full migration runs as a one-time CLI pass when it lands.
