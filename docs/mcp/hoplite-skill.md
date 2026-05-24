# Hoplite skill

[Contract] The SKILL.md body the agent loads when invoked. The skill is named `hoplite` — invoked as `/hoplite` in Claude Code.

## Status

This is the drafted SKILL.md body ready to ship day one. When the implementation lands, this content becomes the actual skill file at the plugin's skill location and loads when the agent invokes `/hoplite` or when the host auto-loads it on first interaction with a Hoplite corpus.

The contract here references entities and tools from [data-model.md](data-model.md) and [tool-api.md](tool-api.md). It declares the protocol the agent follows for every interaction with the graph — this skill orchestrates the agent's use of the corpus.

---

# Hoplite

The corpus is a labeled multigraph stored as files. Nodes are notes; edges are typed relationships between nodes; labels are virtual nodes grouping members. Use this skill's protocol for every interaction with the graph.

## Tools

- `hoplite_init_corpus()` — initialize a fresh corpus at the server's working directory. Creates `.hoplite/` index folders, the SQLite database, and the four shipped envelope files. Idempotent — safe to re-run. Required first call if every other tool errors with "corpus not initialized."
- `hoplite_match_nodes(predicate, k=5)` — find landings. Returns up to `k` `Landing` records (id, summary, labels, score) ranked by relevance. `predicate` is `{text?, node_labels?}` — at least one must be supplied. `text` (BM25-scored) finds nodes similar to a phrase; `node_labels` is a label expression like `note & mcp` or `(note | journal) & !draft`.
- `hoplite_traverse_nodes(from_, depth=1, predicate)` — breadth-first walk. Returns `TraversalHit` records from layers 1 through `depth`, excluding the origin. Default `depth=1` returns the immediate neighbors.
- `hoplite_invoke_node(id)` — invoke a node as a directive. Returns the body with the framing envelope applied (framing prose plus stacked label bodies plus the node body).
- `hoplite_read_node(id)` — read a node as content. Returns the body framed by the fixed content envelope (label-independent), telling the agent to treat the payload as data rather than directive.
- `hoplite_insert_node(id, body, labels=[], out_edges=[])` — create a new node. Rejects if the id already exists.
- `hoplite_update_node(id, body, labels=[], out_edges=[])` — modify an existing node. Rejects if the id doesn't exist.
- `hoplite_index_node(id, labels=[], out_edges=[])` — index a node from a pre-existing file. Reads the body from disk rather than writing it. Useful when the file was created out-of-band, or for re-indexing after a hand-edit.
- `hoplite_delete_node(id)` — remove a node. Drops the node's content, metadata, and all of its label memberships.
- `hoplite_apply_framing(label, content)` — create or replace the envelope prose for a label. Use to set framing on labels beyond the four shipped envelopes.
- `hoplite_slugify_text(s)` — pure function. Normalizes a string into canonical kebab-case `[a-z0-9-]` form. Call it when you need to derive a canonical id or label from human-supplied input before passing to other tools.

## First run

If any tool other than `hoplite_init_corpus` returns "corpus not initialized at `<cwd>`," call `hoplite_init_corpus()` once to set up the index and bootstrap envelopes. Subsequent tool calls work immediately — no restart needed.

## Protocol — aid-station traversal

Enter the graph through `hoplite_match_nodes` when you need to find a starting point, or by direct id when you know what you want. Then walk one step at a time: invoke a node (or read it, if you need its content as data), inspect its out_edges, decide which to follow, retrieve the next.

Typical flow:

1. `hoplite_match_nodes({text: "phrase describing what you need"})` — returns candidate landings.
2. Inspect the landings; pick one based on summary and labels.
3. `hoplite_invoke_node(landing_id)` — read the framed content. Note the out_edges.
4. Decide: does this answer the user, or do you need to go further?
5. If further: pick an edge from out_edges, `hoplite_invoke_node(target_id)`, repeat.
6. Use `hoplite_traverse_nodes(node_id)` (default depth=1) to preview the immediate neighbors without invoking each.

## Reading versus invoking — the verb is the intent

The choice between `hoplite_invoke_node` and `hoplite_read_node` is a declaration. Both verbs frame the response; the verb you call picks which frame.

- `hoplite_invoke_node(id)` applies the imperative envelope appropriate to the node's framing-axis label. An `instruction` node invoked this way means "I am prepared to follow this." A `reference` node invoked this way means "I am prepared to factor this into reasoning." An `observation` node invoked this way means "I am prepared to treat this as historical context."
- `hoplite_read_node(id)` applies the content envelope — fixed, label-independent. The node returns as data: text to inspect, edit, refactor, parse, or extract from. The content envelope overrides whatever framing the node's labels would otherwise carry; an `instruction` node read this way is just text.

Parallel to Claude Code's existing surface: `hoplite_invoke_node` is `/skill` (active skill loading, governs the next response); `hoplite_read_node` is `@file` (file as content, doesn't compel behavior). The verb declares the intent; there's no afterward-decision.

## Writing

Use `hoplite_insert_node(id, body, labels, out_edges)` for new nodes, `hoplite_update_node(id, ...)` to modify existing ones, `hoplite_index_node(id, ...)` to ingest a pre-existing file on disk, `hoplite_delete_node(id)` to remove. Conventions:

- Notes are pure markdown — no frontmatter. The body shape: `# Title` on line 1, blank line 2, one-sentence summary on line 3, blank line 4, body sections from line 5. The indexer parses line 3 as the cached summary.
- Ids are path expressions with extension: `foo.md` for a root-level note, `notes/skill-composition.md` for a categorized note, `journal/2026-05-24-today-was-warm.md` for a journal entry. Each path segment is lowercase kebab-case.
- The first path segment becomes an auto-derived label: `journal/...` carries `journal`, `notes/...` carries `notes`, `mcp/...` carries `mcp`. Root-level ids get no auto-derived path label.
- Filenames matching `<iso-date>-<slug>.<ext>` get the date as an auto-derived label automatically — works for observations and journal entries.
- Use `[[wiki-link]]` in the body to reference another node — wiki-links use the same id form (including extension and path): `[[journal/2026-05-24-foo.md]]`, `[[mcp/data-model.md]]`. The indexer emits `:mentions` edges automatically.
- Body wiki-links produce `:mentions` edges automatically. The `out_edges` parameter on `hoplite_insert_node`/`hoplite_update_node`/`hoplite_index_node` accepts any authored edge object with `type` and `to` fields (no `source` — that's reserved for server-derived edges, including the MinHash-derived `:related` edges materialized on every write). Day one this includes authored `:related` if you want to declare an explicit relatedness edge alongside the MinHash-derived ones; future edge types beyond `:mentions` and `:related` land here too.

## Vocabulary

- node — a content unit identified by id.
- edge — a typed connection between two nodes (`mentions`, `related`); has `type`, `to`, optional `confidence`, optional `source`.
- label — a named set of nodes. Carries an id, optional summary, optional envelope prose (the body the loader inlines during `hoplite_invoke_node`), and a member list. Use `hoplite_apply_framing` to add or update envelope prose.
- landing — a node returned by `hoplite_match_nodes`. A role, not a type.
- framing label — `instruction`, `reference`, or `observation`. The server wraps `hoplite_invoke_node` responses with the framing label's envelope; `hoplite_read_node` ignores the framing label and applies the fixed content envelope. At most one framing label per node. Use `hoplite_apply_framing` to add envelope prose to any other label — including overriding the shipped envelopes for the three framing-axis labels.
