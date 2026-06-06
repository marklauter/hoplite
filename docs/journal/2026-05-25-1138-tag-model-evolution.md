---
title: Tag model evolution — edges then virtual nodes then properties
summary: Three acts on what tags are in the graph. Act one — tags as edges from documents to tag-things. Act two — tags as first-class virtual nodes with their own identity and outbound edges. Act three — tags as property values on documents, no separate entity. Each step solved the prior step's problem and surfaced the next.
tags: [journal, hoplite, tags, ontology, decision]
created: 2026-05-25
---

# Tag model evolution — edges then virtual nodes then properties

Three acts on what tags are in the graph. Act one — tags as edges from documents to tag-things. Act two — tags as first-class virtual nodes with their own identity and outbound edges. Act three — tags as property values on documents, no separate entity. Each step solved the prior step's problem and surfaced the next.

## Act one — tags as edges

Going into the runtime thesis ([[docs/journal/2026-05-21-0401-mcp-runtime-thesis-and-hello-world.md]]), tags lived in document frontmatter as a list: `tags: [skills, mcp, design]`. The indexer's job was to make that list queryable across the corpus. The first instinct: emit an edge for each tag occurrence. A document carrying `tags: [skills]` produces an edge from the document to a node identified by `skills`.

This worked for membership queries — "all documents tagged X" becomes "all sources of edges into the X node." But the tag-side was thin. The X node carried no content, no metadata, no identity beyond its name. It existed as an edge endpoint, nothing more. Two questions immediately surfaced:

- What is the tag node? It has a name. Does it have a body? A description? A landing page?
- How does the agent reach the tag? Via `match_nodes` on the name? Via some separate enumeration tool?

Tags-as-edges treated the tag as a pure relationship without giving it the substance that a query target needs.

## Act two — tags as virtual nodes

The runtime thesis pushed tags into being first-class nodes:

> Categorical membership becomes a node type rather than a flat property or a virtual lookup. Every tag has a sidecar at `docs/index/<tag>.md`, carries the `:Tag` label, owns its membership outbound, and serves as a landing page the agent reaches through `find_entry`.

Tags now had:

- Identity. Each tag was a graph node with a stable id.
- Storage. The tag had a sidecar file on disk carrying its metadata (summary, parent tags for hierarchy).
- Outbound edges. The tag held `:contains` edges (later `member` edges) outward to its member documents. Adding a doc to a tag created an edge from the tag-node side; removing dropped it.
- Optional content. A tag could carry a markdown body — a landing page explaining what the tag covered.

This model survived the data-model spec drafting and the cold-review iteration ([[docs/journal/2026-05-23-1807-data-model-spec-and-cold-review-iteration.md]]). The spec at one point spent ~50 lines on tag-node sidecar shape, label envelopes, members-folder structure as a filesystem-based inverted index — every detail of how a tag-as-node would live on disk and how the indexer would maintain it.

The model also acquired a second job: envelope framing. Three "framing-axis labels" — `instruction`, `reference`, `observation` — became tag-nodes whose body content was the prose envelope the MCP server applied on `invoke` retrieval. See [[docs/journal/2026-05-25-0046-label-as-envelope-death.md]] for that thread's separate fate.

The problems that accumulated:

- A tag's content (its summary, its landing prose) lived in a separate file from any document. Authoring a tag was a different workflow than authoring a document. The mental model fragmented.
- The membership index required maintenance. The folder-of-marker-files pattern handled atomic adds and removes, but the recovery story for partial writes was complicated.
- The framing-axis-label dual role on three specific tags felt forced. Why did `instruction` get a special storage shape and behavior, while `mcp` (also a tag) was just a tag?
- The schema kept growing. Auto-derived labels (from filename prefixes), author-supplied labels, framing-axis labels, topic labels, label hierarchies, label envelopes — every concern got a sub-distinction in the label model.

The first signal that the model was over-committed: the cold-review pass on the data-model spec flagged that mixing markdown frontmatter and YAML sidecars in the same file was a category error. The fix split file roles — sidecar pure YAML, notes pure markdown — which made the tag-node-with-sidecar machinery more explicit and easier to reason about, but also exposed how much machinery there was.

## Act three — tags as properties

The redesign on the morning of 2026-05-25 ([[docs/journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools.md]]) collapsed the retrieval tools and made Hoplite "dataview over documents." Tags survived this pass as virtual nodes; the `Tag` dataclass stayed in the in-memory graph; the `member` edge type from doc to tag stayed.

But the redesign had killed the envelope-framing rationale for the special tag subset. With `invoke_node` and `read_node` retired, the framing-axis labels lost their special behavior. They became regular tags. And once they were regular tags, the question came back: what does a tag-as-node actually buy?

The EAV refactor ([[docs/journal/2026-05-25-1137-eav-property-graph-refactor.md]]) answered: not enough to justify the complexity. The new shape:

- `documents` table holds identity and immutable bookkeeping.
- `node_properties(node_id, key, value)` holds every frontmatter field.
- Tags become rows in `node_properties` with `key='tags'` and `value=<tag-slug>`. A doc with three tags has three rows.

Tag membership becomes a property query: `SELECT node_id FROM node_properties WHERE key='tags' AND value=<slug>`. No tag-node. No `member` edge. No sidecar. No envelope.

What this collapsed:

- The `member` edge type. Two edge types remain: `mentions` (wikilinks) and `related` (MinHash). Document-to-document only.
- The `Tag` dataclass as a distinct entity in the in-memory graph.
- Any per-tag storage shape on disk.
- The argument about what a tag's body would carry.

What this preserved:

- Tag queries still work. The query pattern (`tagged: skills & !draft`) is unchanged from the outside.
- Authored tag lists in frontmatter still produce the same surface: a tag named `skills` is queryable as `skills` regardless of which model the indexer uses internally.
- The corpus didn't have to change. The 30 docs that had been backfilled with frontmatter the previous day kept their tags as written; the new indexer read them into property rows instead of edge rows.

## Why the journey was worth taking

Each act solved a real problem from its predecessor:

- Act two solved act one's "what is a tag?" problem by giving tags identity and storage.
- Act three solved act two's "tag schema keeps growing" problem by removing tag identity entirely. A tag is a string in a property table; there is no shape to commit to beyond a string.

Going straight from act one to act three would have skipped the diagnostic. The over-built virtual-node model was what made the property model legible — it showed exactly which capabilities the simpler model could drop and which had to be preserved by other means (property predicates instead of edge traversal).

## What this changed for the agent surface

Nothing visible. The agent calls `match_nodes(predicate={"tagged": "skills"})` the same way regardless of internal model. The skill body teaches "tags are properties on documents" because that's the current truth, but a user who learned an earlier version reads the new docs and finds their queries still work.

The cost of getting the model wrong was internal — every model change touched the walker, the dump schema, the test suite, the skill prose. The benefit of getting it right was external: agents don't pay attention to internal model churn, but they pay a real cost on every schema change to the surface they call. Settling the property model meant the next schema change wouldn't have to touch the tag query path.

## Cross-references

- `[[journal/2026-05-21-0401-mcp-runtime-thesis-and-hello-world]]` — where act one and act two crystallized.
- `[[journal/2026-05-23-1807-data-model-spec-and-cold-review-iteration]]` — peak commitment to act two.
- `[[journal/2026-05-25-0202-dead-then-redesign-in-memory-graph-and-four-tools]]` — the redesign that kept act two alive but stripped its envelope-framing rationale.
- `[[journal/2026-05-25-1137-eav-property-graph-refactor]]` — act three lands.
- `[[journal/2026-05-25-0046-label-as-envelope-death]]` — the parallel collapse of envelope framings that ran adjacent to this tag-model arc.
