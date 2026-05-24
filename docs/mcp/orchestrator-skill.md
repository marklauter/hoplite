# Orchestrator skill

[Contract] The SKILL.md body the agent loads on first interaction with the graph.

## Status

This is the drafted SKILL.md body ready to ship day one. When the implementation lands, this content becomes the actual skill file at the plugin's skill location and loads automatically the first time the agent interacts with the corpus.

The contract here references entities and tools from [data-model.md](data-model.md) and [tool-api.md](tool-api.md). It declares the protocol the agent follows for every interaction.

---

# Knowledge graph orchestrator

The corpus is a labeled multigraph stored as files. Nodes are notes; edges are typed relationships between nodes; labels are virtual nodes grouping members. Use this skill's protocol for every interaction with the graph.

## Tools

- `match(predicate, k=5)` — find landings. Returns up to `k` `Landing` records (id, summary, labels, score) ranked by relevance to the predicate.
- `invoke(id)` — invoke a node as a directive. Returns the body with the framing envelope applied (framing prose plus stacked label bodies plus the node body).
- `read(id)` — read a node as content. Returns the body framed by the fixed content envelope (label-independent), telling the agent to treat the payload as data rather than directive.
- `insert(id, body, labels=[], out_edges=[])` — create a new node. Rejects if the id already exists.
- `update(id, body, labels=[], out_edges=[])` — modify an existing node. Rejects if the id doesn't exist.
- `index(id, labels=[], out_edges=[])` — index a node from a pre-existing file. Reads the body from disk rather than writing it. Useful when the file was created out-of-band, or for re-indexing after a hand-edit.
- `delete(id)` — remove a node. Drops the node's content, metadata, and all of its label memberships.
- `apply_framing(label, content)` — create or replace the envelope prose for a label. Use to set framing on labels beyond the four shipped envelopes.
- `slugify(s)` — pure function. Normalizes a string into canonical kebab-case `[a-z0-9-]` form. Call it when you need to derive a canonical id or label from human-supplied input before passing to `insert`/`update`/`apply_framing`.
- `traverse(from, depth=1, predicate)` — breadth-first walk. Returns up to `depth` layers of `TraversalHit` records, excluding the origin. Default `depth=1` returns the immediate neighbors.

## Protocol — aid-station traversal

Enter the graph through `match` when you need to find a starting point, or by direct id when you know what you want. Then walk one step at a time: invoke a node (or read it, if you need its content as data), inspect its out_edges, decide which to follow, retrieve the next.

Typical flow:

1. `match("phrase describing what you need")` — returns candidate landings.
2. Inspect the landings; pick one based on summary and labels.
3. `invoke(landing_id)` — read the framed content. Note the out_edges.
4. Decide: does this answer the user, or do you need to go further?
5. If further: pick an edge from out_edges, `invoke(target_id)`, repeat.
6. Use `traverse(node_id)` (default depth=1) to preview the immediate neighbors without invoking each.

## Reading versus invoking — the verb is the intent

The choice between `invoke` and `read` is a declaration. Both verbs frame the response; the verb you call picks which frame.

- `invoke(id)` applies the imperative envelope appropriate to the node's framing-axis label. An `instruction` node invoked this way means "I am prepared to follow this." A `reference` node invoked this way means "I am prepared to factor this into reasoning." An `observation` node invoked this way means "I am prepared to treat this as historical context."
- `read(id)` applies the content envelope — fixed, label-independent. The node returns as data: text to inspect, edit, refactor, parse, or extract from. The content envelope overrides whatever framing the node's labels would otherwise carry; an `instruction` node read this way is just text.

Parallel to Claude Code's existing surface: `invoke` is `/skill` (active skill loading, governs the next response); `read` is `@file` (file as content, doesn't compel behavior). The verb declares the intent; there's no afterward-decision.

## Writing

Use `insert(id, body, labels, out_edges)` for new nodes, `update(id, ...)` to modify existing ones, `index(id, ...)` to ingest a pre-existing file on disk, `delete(id)` to remove. Conventions:

- Notes are pure markdown — no frontmatter. The body shape: `# Title` on line 1, blank line 2, one-sentence summary on line 3, blank line 4, body sections from line 5. The indexer parses line 3 as the cached summary.
- Ids are path expressions with extension: `foo.md` for a root-level note, `notes/skill-composition.md` for a categorized note, `journal/2026-05-24-today-was-warm.md` for a journal entry. Each path segment is lowercase kebab-case.
- The first path segment becomes an auto-derived label: `journal/...` carries `journal`, `notes/...` carries `notes`, `mcp/...` carries `mcp`. Root-level ids get no auto-derived path label.
- Filenames matching `<iso-date>-<slug>.<ext>` get the date as an auto-derived label automatically — works for observations and journal entries.
- Use `[[wiki-link]]` in the body to reference another node — wiki-links use the same id form (including extension and path): `[[journal/2026-05-24-foo.md]]`, `[[mcp/data-model.md]]`. The indexer emits `:mentions` edges automatically.
- Body wiki-links produce `:mentions` edges automatically. The `out_edges` parameter on `insert`/`update`/`index` accepts any authored edge object with `type` and `to` fields (no `source` — that's reserved for derived edges from reindex). Day one this includes `:related` if you want to declare an authored relatedness edge; future edge types beyond `:mentions` and `:related` land here too.

## Vocabulary

- node — a content unit identified by id.
- edge — a typed connection between two nodes (`mentions`, `related`); has `type`, `to`, optional `confidence`, optional `source`.
- label — a named set of nodes. Carries an id, optional summary, optional envelope prose (the body the loader inlines during `invoke`), and a member list. Use `apply_framing` to add or update envelope prose.
- landing — a node returned by `match`. A role, not a type.
- framing label — `instruction`, `reference`, or `observation`. The server wraps `invoke` responses with the framing label's envelope; `read` ignores the framing label and applies the fixed content envelope. At most one framing label per node. Use `apply_framing` to add envelope prose to any other label — including overriding the shipped envelopes for the three framing-axis labels.
