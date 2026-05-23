# File-based implementation

[Implementation, day-one] How the contracts in this folder map onto a filesystem. The shipping default for day one.

## Storage layout

One authored directory; the index is a flat sidecar tree plus a label inverted-index subdirectory.

```
docs/notes/<slug>.md                            authored note (pure markdown, body only)
docs/notes/<iso-date>-<slug>.md                 authored note with observation or journal label
docs/index/<id>.yml                             node sidecar (pure YAML, structured metadata)
docs/index/labels/<label>.yml                   label sidecar (pure YAML, structured metadata)
docs/index/labels/<label>.md                    label envelope (pure markdown, optional prose)
docs/index/labels/<label>/<member-id>           empty membership marker (filename is the data)
docs/index/envelopes/read.md                    fixed content envelope applied by read()
docs/index/embeddings/<id>.npy                  embedding blob (when reindex lands)
```

Each file type has one job. `.md` files carry human-readable content — notes and label envelope prose. `.yml` files carry structured metadata the indexer reads and writes. Empty marker files carry membership in their filename. The split matches the access pattern: sidecars are the indexed "B-tree" surface (small, scanned often); notes are the "BLOB" (larger, opened only when the content is needed via `invoke` or `read`).

## Entity-to-file mapping

How each entity from [data-model.md](data-model.md) is realized on disk.

### Node

Two files per node:

- Authored content: `docs/notes/<id>.md`. Pure markdown body, no YAML frontmatter. The body shape on lines 1-4 is fixed: `# Title` on line 1, blank on line 2, summary on line 3, blank on line 4, body sections from line 5 onward. The indexer parses line 3 as the cached summary.
- Sidecar metadata: `docs/index/<id>.yml`. Pure YAML, no markdown wrapper. Carries `id`, `labels`, `out_edges`, `summary`, optional `in_edges`, optional `embedding`. No `body` field — content lives in the authored file.

The two files store disjoint fields: note has body, sidecar has metadata. There is no field-level conflict to resolve.

### Label

Up to three files per label, each independent:

- `docs/index/labels/<label>.yml` — label sidecar with `id`, optional `summary`, optional `out_edges`. Created with the first member.
- `docs/index/labels/<label>.md` — label envelope, the `envelope_body` from the data model. Optional; only present if there's authored prose to inline.
- `docs/index/labels/<label>/` — members folder containing one empty marker file per member, named exactly the member's id.

Membership IS the filesystem. Adding a node to a label creates `docs/index/labels/<label>/<id>` (atomic file creation). Removing drops the file (atomic unlink). Listing members is `os.listdir` over the folder.

The three siblings coexist on disk distinguished by suffix: `.yml` is the metadata, `.md` is the envelope prose, the trailing-slash form is the members folder. The implementer discriminates by suffix.

### Edge

Edges live as YAML objects inside their source node's `out_edges` array (in the node sidecar `.yml`). Symmetric `:related` edges are written to both endpoints' sidecars.

### Envelope

The framing component comes from a label's envelope file (`docs/index/labels/<label>.md`). For `read`, it comes from the fixed `docs/index/envelopes/read.md`. The structured `Envelope` shape in the data model is composed by the server at retrieval time; on disk it's just the contributing files.

## Id and filename rules

A node's id is its filename without the `.md` extension. `docs/notes/foo.md` has id `foo`; `docs/notes/2026-05-22-design-meeting.md` has id `2026-05-22-design-meeting`. The sidecar always lives at `docs/index/<id>.yml`.

Filename convention. Nodes carrying `observation` or `journal` labels use the ISO date prefix — `docs/notes/<iso-date>-<slug>.md`. The indexer parses the prefix to derive the date label. Other nodes use `docs/notes/<slug>.md`. The prefix is the single source of truth for the date; no separate `date:` frontmatter field.

The date prefix prevents collisions on recurring topics: working on the same refactor across journal sessions yields `2026-05-22-refactor-to-ef-core` and `2026-05-23-refactor-to-ef-core` as distinct ids.

Date label is derived only when the node carries `observation` or `journal`. If an author removes both labels while keeping the date-prefixed filename, the indexer drops the date label on the next write; the prefix in the filename becomes cosmetic. The id stays stable — the filename doesn't get renamed implicitly.

Slug derivation matches the canonical rule: lowercase, whitespace to hyphens, strip non-alphanumeric except hyphens. The `slugify` tool and any `slugify.sh` script share this rule.

## Corpus root configuration

The paths above (`docs/notes/`, `docs/index/`) are the default layout. The MCP server reads a `corpus_root` config value at startup; everything is computed relative to it. This future-proofs multi-corpus setups and relocated layouts without touching code.

## Why this shape

Flat sidecar storage. A node carries a multi-valued labels set, so directory-by-label cannot place it — the node belongs to several labels at once. Flat storage gives O(1) path lookup from id; per-label files in `labels/` provide the inverted index that "all nodes labeled X" queries need.

No separate framings directory. Framings collapse into labels. `instruction`, `reference`, `observation` are just three labels whose envelope files at `docs/index/labels/<framing>.md` carry the framing prose. The server knows a hardcoded list of "framing-axis labels" to drive envelope selection on `invoke`, but the data model has no separate framing concept.

Folder-per-label membership. Each member is its own file means atomic create/unlink per member, no shared list to contend on, `ls` is the inverted index. The phase-two multi-writer goal benefits — no per-label contention.

## Insert and update flow

What `insert(id, body, labels, out_edges)` and `update(id, body, labels, out_edges)` do, in order. Step 0 differs between them; the rest is shared.

0. Existence check. `insert` rejects if `docs/notes/<id>.md` already exists; `update` rejects if it doesn't.
1. Validate labels. Per [behavior.md](behavior.md#validation-and-error-model).
2. If labels include `observation` or `journal`, verify the id has an ISO date prefix. Reject if missing.
3. Validate `out_edges`. Reject any author-supplied edge that carries a `source` field.
4. Write the authored note at `docs/notes/<id>.md`. Pure markdown — no frontmatter. Body shape as described above.
5. Parse `[[wiki-links]]` from the body; emit a `:mentions` edge for each into the sidecar's `out_edges`.
6. Reconcile `out_edges` per the rule in [behavior.md](behavior.md#edge-reconciliation-on-update). On `insert`, no prior state — just merge parsed mentions with author-supplied. On `update`, preserve derived edges.
7. Compose auto-derived labels: `note`, plus the ISO date label if applicable.
8. Parse the cached summary from the body — line 3 (after the H1 and its blank line).
9. Write the sidecar at `docs/index/<id>.yml` with the full labels list, reconciled out_edges, and cached summary.
10. For each label the node now carries, ensure the label sidecar and the membership marker exist. If the label is new (no sidecar present), create `docs/index/labels/<label>.yml` with `id: <label>` and empty optional fields. Then create the empty marker file at `docs/index/labels/<label>/<id>`. Atomic create-if-not-exists for both. Create the folder if it doesn't exist.
11. For each label the node previously carried but no longer does (`update` only), unlink the marker file at `docs/index/labels/<label>/<id>`.
12. Return `WriteResult` with id and any warnings.

## Delete flow

What `delete(id)` does:

1. Existence check. Reject if `docs/notes/<id>.md` doesn't exist.
2. Read the sidecar's labels list to know which membership folders the node was in.
3. Unlink `docs/notes/<id>.md`.
4. Unlink `docs/index/<id>.yml`.
5. For each label the node carried, unlink `docs/index/labels/<label>/<id>`.
6. Return `WriteResult` with id and any warnings.

Wiki-link references to the deleted id from other notes become dangling and drop silently from query results. Cached back-references in other nodes' `in_edges` and symmetric `:related` edges don't exist day one (reindex deferred); when reindex lands, the next pass reconciles back-references to deleted ids.

## Atomicity

Per-file writes use temp-and-rename so no individual file appears half-written. Cross-file atomicity is best-effort day one — a crash between writing the sidecar and updating a label folder leaves the graph briefly inconsistent until the next `repair` pass reconciles it.

Source of truth is split: notes are authoritative for body content, label-folder markers are authoritative for membership. Sidecars are derived from both, so repair is always possible.

Cross-file transactional semantics arrive later via a write-ahead journal — see [implementation-alternatives.md](implementation-alternatives.md#write-ahead-journal-for-cross-file-atomicity).

## Search day one

`match(predicate, k)` uses BM25 over node bodies and summary fields. The standard relevance formula:

```
score(D, Q) = Σ over each term t in Q:
  IDF(t) · (tf(t,D) · (k1 + 1)) / (tf(t,D) + k1 · (1 − b + b · |D| / avgdl))
```

Defaults: `k1 = 1.5` (term-frequency saturation), `b = 0.75` (length normalization). Tokenize bodies on word boundaries, lowercase, strip punctuation. For each `match()` call, tokenize the predicate, score against every node, sort descending, return the top `k`. O(N · |Q|) per query — fine at hundreds of notes, room for thousands.

Pure Python, no model dependencies. `rank_bm25` is the obvious library choice; hand-rolling is roughly 50 lines if avoiding the dep matters. No inverted index day one — recompute per call. Add one later if corpus size makes per-call rescoring expensive.

## Reindex — deferred, not forgotten

No server-side reindex pass day one. Most of what reindex would do is already reachable through the agent-as-driver pattern: walk `docs/notes/`, call `update(id, body=<current-body>, labels=<current-labels>)` on each, and the existing write-time flow re-parses wiki-links, regenerates the cached summary, rewrites the sidecar, and reconciles label markers. Stale sidecars, hand-edited bodies, and missing derived metadata fix themselves through normal `update` calls. No new primitive needed for the "soft reindex" case.

The features that genuinely need a server-side reindex are the ones the agent can't compute through the existing surface:

- MinHash pairwise relatedness — Jaccard-similarity edges above `minhash_threshold` (0.20 default) materialize as `:related` derived edges with `source: minhash`. Requires corpus-wide signature computation and pairwise comparison.
- Embeddings via local Ollama (`nomic-embed-text` candidate, 768-dim, ~270MB, CPU-fast) writing `.npy` files into `docs/index/embeddings/`. With embeddings, `match` switches from BM25 to vector similarity, and embedding-derived `:related` edges supplement MinHash.

These two are the actual day-two reindex scope. The trigger model (manual CLI, scheduled, file-watch, write-trigger-drain) is decided when reindex itself is built. None of the day-one tools depend on reindex; the graph functions fully without it.

## Bootstrap — shipped envelope files

Four envelope files arrive as bundled assets the plugin installer drops into place at install time:

- `docs/index/envelopes/read.md`
- `docs/index/labels/instruction.md`
- `docs/index/labels/reference.md`
- `docs/index/labels/observation.md`

The exact prose for each is in [behavior.md](behavior.md#day-one-envelope-prose).

After install they are editable like any other authored file — by hand, or via `apply_framing` for the three framing-axis envelopes. The `read` envelope is structurally separate and only edits through hand-edit or repair.

Framing on any non-shipped label is optional. If `docs/index/labels/<label>.md` exists, the loader inlines it during `invoke`; if it doesn't, the label contributes nothing to the envelope (the membership still applies — only the prose contribution is conditional). `read` always inlines `docs/index/envelopes/read.md`; if missing, `read` errors — the contract is load-bearing.

## Failure modes

### Mid-flight crashes

A single `insert` or `update` call touches up to 2 + N files — the authored note, the sidecar, and one empty membership marker file per label the node carries (plus unlinking markers for labels removed on an update). A `delete` call unlinks the authored file, the sidecar, and the membership markers in every label folder the node was in.

The authored note and sidecar use temp-and-rename so they never appear half-written. Membership markers are atomic creates (empty files) and unlinks. Cross-file atomicity across the full set is not guaranteed day one — a crash between marker writes leaves the membership view briefly inconsistent.

Day-one recovery. The source of truth is split: `docs/notes/<id>.md` is authoritative for body content; the label membership markers in `docs/index/labels/<label>/<id>` are authoritative for membership. The sidecar is a derived projection of both. The operational `repair` CLI regenerates sidecars by reading body content from the note and label membership from the folder markers; if a sidecar's labels list disagrees with the folder markers, the folder markers win.

Repair-on-read is scoped, not blanket. It fires only on operations that actually consult a label's membership — listing or filtering members of `docs/index/labels/<label>/` triggers a check against the folder. Node fetches via the private fetch primitive do not validate label markers; the consistency check rides only on the path that depends on the data.

### Read failures

- Missing id: `invoke`, `read`, `traverse(from=missing)` return an error. "Missing" means no authored file at `docs/notes/<id>.md` — the node was never inserted or has been deleted.
- Missing sidecar with authored file present: the indexer surfaces an error noting the sidecar is absent. The body is still readable from the authored file, so the result can carry the body alongside the error for the caller's use. Auto-repair on this path is deferred — for day one, surface the inconsistency and let the operational `repair(id)` CLI rebuild.
- Corrupt sidecar (YAML parse fails): rebuild via the operational `repair(id)` CLI. The sidecar is fully derivable from the authored note plus the label folders that contain a marker for this id.
- Dangling out_edge target: `invoke(target)` returns an error when the reader follows the edge. The indexer doesn't pre-validate edge targets at read time.

### Concurrency

Day one assumes a single writer. Simultaneous writes to the same node id risk last-write-wins on the authored file and sidecar; simultaneous writes touching the same label cannot collide on membership because each member is its own file (different filenames don't contend, and same-filename creation is atomic via O_EXCL).

Multi-agent support is the actual target — single-writer is just the day-one simplification. Lifting it is the first priority for the second pass. See [implementation-alternatives.md](implementation-alternatives.md#multi-writer-support).

### Inconsistency recovery

When the index disagrees with the authored corpus, the authored corpus wins. An operational `repair(scope)` CLI handles recovery:

- For one node: regenerate its sidecar from the authored note plus the label-folder markers that reference its id.
- For all nodes: walk `docs/notes/` to enumerate notes; walk `docs/index/labels/*/` to enumerate memberships; regenerate every sidecar from those two sources. Drop label-folder markers that point at non-existent notes (orphans from deleted notes that weren't fully cleaned).

Full-corpus repair is the "I broke the index" escape hatch — slow but always correct.

## Worked example — node sidecar

The sidecar at `docs/index/mcp-server-as-skill-system-runtime.yml`:

```yaml
id: mcp-server-as-skill-system-runtime
labels: [note, architecture, mcp, skills]
out_edges:
  - type: mentions
    to: prototype-the-plugin-mcp-server-in-python
  - type: mentions
    to: writing-prose
  - type: related
    to: skill-composition-foundation-and-downstream
    confidence: 0.62
    source: minhash
summary: the MCP server as runtime for a knowledge-graph-backed skill system
embedding: docs/index/embeddings/mcp-server-as-skill-system-runtime.npy
```

The authored content lives at `docs/notes/mcp-server-as-skill-system-runtime.md` — pure markdown body, no frontmatter.

## Worked example — label with all three pieces

The label sidecar at `docs/index/labels/instruction.yml`:

```yaml
id: instruction
summary: operative guidance the agent should follow
```

The envelope prose at `docs/index/labels/instruction.md`:

```markdown
The following is operative guidance for your current task. Apply it directly to your next response. Read it as you would read an active section of your system prompt — not as background reading, not as one perspective among many.
```

The members folder at `docs/index/labels/instruction/`:

```
docs/index/labels/instruction/
  orchestrator-skill
  taking-notes
  writing-prose
```

Each marker file is empty.

## Worked example — label with members only, no envelope

For tracking a thread without an authored landing page, the envelope `.md` is absent; the sidecar exists for the id and summary; the members folder lists the thread:

```
docs/index/labels/audit-mode-followup/
  2026-04-12-audit-mode-thinking
  2026-04-15-audit-mode-prototype
  2026-05-03-audit-mode-decision
```

Listing members is `ls`; the inverted index is the filesystem itself.

## Migration — deferred

The current `docs/notes/` corpus predates the graph shape (no sidecars, no label inverted indexes). Migration to the new shape requires a converter that walks every note, derives labels from filenames and existing frontmatter, and produces sidecars and label files. Deferred — when migration lands, it runs as a one-time CLI pass that produces the initial index from existing content. Day-one development can use a fresh empty corpus or a hand-curated subset.

## Rename semantics

Slug change means three writes plus a grep: rename the authored file, rename the sidecar at `docs/index/<id>.yml`, grep the corpus for `[[old-slug]]` references and rewrite them. Tooling can automate the grep-and-replace; a `rename_node(old, new)` MCP call is a candidate for the indexer's surface.

## YAML conventions

The YAML parser uses strict mode (no implicit type coercion), with string values quoted in the writer to avoid the Norway-style gotchas — bare `NO`, `Y`, `OFF` would coerce to booleans, version-like strings to floats.
