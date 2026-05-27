## Hoplite

Hoplite is a graph over the markdown corpus at `docs/`. Each `.md` file is a document; YAML frontmatter at the top of each file feeds the index. Hoplite builds the graph in memory at MCP server startup.

Hoplite is the index; your built-in `Read`, `Write`, `Edit`, and `Bash rm` tools are the content surface.

### Tools

- `where(predicate, k=5)` — search. Returns up to `k` `Hit` records (path, summary, tags, score) ranked by relevance. `predicate` is `{text?, tagged?}` — at least one required. `text` is BM25-scored over body and summary. `tagged` is a tag expression like `notes`, `notes & mcp`, or `(notes | journal) & !draft`.
- `relatives(from_, predicate=None, depth=1)` — breadth-first walk from a starting document. Returns `TraversalHit` records (path, summary, tags, distance, via_edges) for nodes at distance 1 through `depth` from the origin. Predicate fields (all optional): `edge_types` (filter by edge kind — `mentions`, `related`), `min_confidence`, `direction` (`out`/`in`/`both`), `tagged` (tag expression filter on reached documents).
- `refresh()` — rebuild the in-memory graph from the current state of the corpus. Call after writes so subsequent queries see the changes.
- `export(path=None)` — debug. Snapshots the in-memory graph to a SQLite file (default `.hoplite/<ISO-timestamp>.index.sqlite` — each dump is uniquely named so prior snapshots survive). Then you can `Bash sqlite3 .hoplite/<file>` for arbitrary SQL exploration.

### Edges

Two edge kinds materialize. Edges connect documents to documents only — tag membership is a property, not an edge.

- `mentions` — document → document. One per `(source, target)` pair from `[[wikilink]]` occurrences in body text. Multiple wikilinks from one document to the same target collapse to a single edge. Unresolved wikilinks create ghost documents.
- `related` — document ↔ document, symmetric. Emitted by MinHash similarity above threshold. Carries a `confidence` property holding the Jaccard score.

### Vocabulary

- Document — a markdown file in the corpus. Identified by relative path. The only node type day one.
- Tag — a free-form annotation authored in a document's frontmatter `tags:` list. Tags are properties on documents, not separate nodes. Stored casefolded for case-insensitive matching. Query with `tagged: <expression>`.
- Property — a key-value pair from a document's frontmatter. Every YAML field (mandatory or user-defined) becomes one or more property rows on the owning document.
- Ghost document — a wikilink target that exists in the graph alone, with `resolved = false`. Promoted in place when the file lands on disk.
- Hit — a search result from `where`.
- TraversalHit — a result from `relatives`. Carries `distance` and `via_edges`.
- Wikilink — `[[path-or-alias]]` syntax in body text.
