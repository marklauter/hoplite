## Hoplite catalog

Hoplite is a knowledge graph over the markdown corpus at `docs/`. Each `.md` file is a document; YAML frontmatter at the top of each file feeds the index. Hoplite builds the graph in memory at MCP server startup.

Hoplite is the index; your built-in `Read`, `Write`, `Edit`, and `Bash rm` tools are the content surface. `Grep` and `Glob` are the literal surface — substrings in lines and filename patterns. Hoplite is the semantic surface: documents ranked by topical relevance (BM25 FTS over body and summary), filtered by predicate expressions, and reachable through authored `[[wikilink]]` paths (`mentions` edges) or inferred topical adjacency (`related` edges from MinHash similarity).

### Tools

- `where(predicate, k=5)` — rank documents by topical relevance, tag expression, or both. `text` runs BM25 over an FTS index of body and summary, so a query for `caching strategy` surfaces documents *about* caching rather than only lines containing the literal token. `tagged` filters by boolean tag expression: `note`, `note & mcp`, `(note | journal) & !draft`. At least one of `text`/`tagged` required. Returns up to `k` `Hit` records (path, summary, tags, score) ranked by score.
- `relatives(from_, predicate=None, depth=1)` — breadth-first walk from a starting document through authored `mentions` edges and inferred `related` edges. Surfaces neighborhoods the corpus author may or may not have explicitly linked: a `related` edge can connect two topically-adjacent documents with no wikilink between them. Returns `TraversalHit` records (path, summary, tags, distance, via_edges) for nodes at distance 1 through `depth`. Predicate fields (all optional): `edge_types` (`mentions`, `cites`, `related`), `top_k_related` (cap on the number of `related` neighbors followed per node, ranked by confidence — set to narrow the walk to each node's strongest similarities; omit to widen the walk and judge adjacency from the per-edge `confidence` in `via_edges`. `mentions` and `cites` are always followed.), `direction` (`out`/`in`/`both`), `tagged` (tag expression filter on reached documents).
- `refresh()` — rebuild the in-memory graph from the current state of the corpus. Call after writes so subsequent queries see the changes. Returns a `WriteResult` (`path` = corpus root, `warnings`).
- `export(path=None)` — debug. Snapshots the in-memory graph to a SQLite file (default `.hoplite/<ISO-timestamp>.index.sqlite` — each dump is uniquely named so prior snapshots survive). Then you can `Bash sqlite3 .hoplite/<file>` for arbitrary SQL exploration. Returns a `WriteResult` (`path` = snapshot file, `counts` with `documents`/`ghosts`/`edges`, `warnings`).

### Edges

Two edge kinds materialize. Edges connect documents to documents only — tag membership is a property, not an edge.

- `mentions` — document → document. One per `(source, target)` pair from `[[wikilink]]` occurrences in body text. Multiple wikilinks from one document to the same target collapse to a single edge. A `[[docs/<path>.md]]` target that lacks a backing file or a `[[ghost/<slug>]]` target creates a ghost document.
- `cites` — document → URL. One per `(source, url)` pair from inline `[text](https://...)` markdown links in body text. The dst node is keyed by the verbatim URL (no canonicalization); call `relatives(predicate={"edge_types": ["cites"]})` to list every external reference from a document.
- `related` — document ↔ document, symmetric. Emitted by MinHash similarity above threshold. Carries a `confidence` property holding the Jaccard score.

### Vocabulary

- Document — a node in the graph. Identified by its path: `docs/<sub>/<name>.md` for real markdown documents on disk, `ghost/<slug>` for intentional open loops, `https://...` (or `http://`) for URL-keyed nodes auto-indexed from inline markdown links. The same path appears in `Hit.path` and `TraversalHit.path` — for `docs/...` paths the agent can `Read` directly; for URL paths the agent has the URL itself to `WebFetch` or pass on.
- Tag — a free-form annotation authored in a document's frontmatter `tags:` list. Tags are properties on documents, not separate nodes. Stored casefolded for case-insensitive matching. Query with `tagged: <expression>`.
- Property — a key-value pair from a document's frontmatter. Every YAML field (mandatory or user-defined) becomes one or more property rows on the owning document.
- Ghost document — a wikilink target without a backing file (`resolved = false`). Authored as `[[ghost/<slug>]]` for intentional open loops. First-class node in `relatives` results, so the corpus's unwritten cross-references stay visible. Walker injects a synthetic `ghost` tag so `where({"tagged": "ghost"})` enumerates them; URL nodes get a synthetic `url` tag the same way.
- Hit — a search result from `where`. Fields: `path`, `summary`, `tags`, `score`.
- TraversalHit — a result from `relatives`. Fields: `path`, `summary`, `tags`, `distance`, `via_edges`.
- WriteResult — returned by `refresh` and `export`. Fields: `path`, `counts` (optional), `warnings` (optional). The reindex's `warnings` list surfaces malformed wikilink targets (anything not starting with `docs/` or `ghost/`) so you can fix them.
- Wikilink — an in-body cross-reference between documents; materializes a `mentions` edge. Two valid shapes: `[[docs/<path>.md]]` for real refs and `[[ghost/<slug>]]` for intentional open loops.
