---
title: Frontmatter is a typed envelope over the property graph
summary: The design behind the Hoplite frontmatter contract — why keys carry a document./edge. namespace, why title and summary stay bare, how the two spelling axes normalize, how malformed blocks are handled, and the tradeoffs underneath. This note is the source of truth; the shipped frontmatter component is its sparse operational distillation.
document:
  tags: [hoplite, frontmatter, design, spec]
  created: 2026-05-29
---

# Frontmatter is a typed envelope over the property graph

Every document in the corpus opens with a YAML frontmatter block, and every key in it lands somewhere specific in the property graph. This note is the design canon for that contract — the concepts, the tradeoffs, and the reasoning. The shipped operational handbook (`templates/components/shape/frontmatter.md`, mail-merged into the skills and the frontmatter hook) is a deliberately sparse distillation of what follows: it tells an agent what to write, this note says why. When the two disagree, this note wins and the handbook is corrected against it.

## Two graph destinations, declared by namespace

Hoplite is a property graph — nodes (documents) carry properties, and edges connect documents. Frontmatter is the authoring surface for both. Every key beyond `title` and `summary` creates exactly one of two things:

- A node property — a fact stored on the document's own node: a key with one or more values (`status`, `priority`, `tags`).
- An edge stereotype — a labeled link from this document to another: a typed `mentions` edge carrying a name like `blocked_by` or `supports`.

`document` and `edge` are namespaces, and a key's prefix declares which destination it has: `document.<key>` is a node property, `edge.<stereotype>` is an edge. The prefix is mandatory because the destination is not inferable from the key name — `blocked_by` reads equally well as a property or a link, so the namespace resolves the ambiguity at authoring time instead of guessing at parse time.

## Title and summary are bare because they are not properties

`title` and `summary` carry no prefix. They are first-class fields on the node, FTS-indexed for `where` search and returned by every query so a caller scans a hit without opening the file. They are single-valued by construction and live in the `fts` table, not `node_property`. Prefixing them would misfile them as ordinary properties and break the search projection. So the rule reduces to: title and summary bare, everything else namespaced.

## Mandatory and optional fields

Two fields are mandatory; a document missing either is skipped at reindex with a warning, never defaulted:

- `title` (bare string) — short human-readable name.
- `summary` (bare string) — one-line lede.

The mandatory set is exactly the node's first-class FTS fields; nothing in the property bag is required. Optional fields:

- `document.created` — creation timestamp. Optional at the frontmatter layer; `created` is a reserved word defined and validated in the document-graph design (the frontmatter doc states the contract here, not the reserved-word semantics).
- `document.tags` (list) — identity slugs, kebab-case lowercase, casefolded for lookup. A document may carry none. Tags remain the identity mechanism when present (see below); a specific artifact type — a journal entry, say — can still require its own type tag through its skill rather than through this contract.
- `document.aliases` (list) — alternate paths that resolve to this document, added on rename so old wikilinks keep resolving.

`document.tags` and `document.aliases`, being lists, follow the omit-when-empty rule: include the key only when it carries at least one element, and omit it otherwise; an empty list is valid for neither.

There is deliberately no `updated` field. Modification time drifts from reality after git checkouts and file copies, and a hand-maintained date lies the moment someone forgets to bump it. Git history is the authoritative modification record; `document.created`, when supplied, is the stable authored creation timestamp.

## Two independent spelling axes

A key carries spelling freedom on two axes that authors conflate but the parser treats separately.

The namespace axis is dotted or nested:

```yaml
document.tags: [note, design]
```

```yaml
document:
  tags: [note, design]
```

These are different YAML structures — `document.tags` is one key containing a dot; the nested form is a mapping under `document`. Hoplite's parser flattens the nested mapping to dotted keys, so the two are equivalent by Hoplite's rule, not YAML's. Neither is preferred, and a file may mix them — a nested `document:` block beside dotted `edge.<stereotype>` lines.

The list axis is flow or block sequence, which YAML itself parses to the same list:

```yaml
document.tags: [note, design]
```

```yaml
document.tags:
  - note
  - design
```

`document.tags`, `document.aliases`, and every `edge.<stereotype>` must be sequences. Any other `document.<key>` may be a bare scalar — `document.status: draft` stores as a single-value property, identical to `document.status: [draft]`.

The inline wikilink form of a stereotype keeps a colon rather than a dot — `[[supports:docs/notes/foo.md]]` — because filesystem paths contain dots (file extensions) but cannot contain colons, so the colon splits unambiguously inline while the dot splits unambiguously in a frontmatter key. This inline form is designed but not yet wired: the wikilink extractor does not split the colon today, so authoring it now produces a malformed target, not a stereotyped edge. Its full treatment belongs with the graph and stereotype design.

## Tags classify; properties carry state

A tag answers "what is this document?" — immutable identity: its type, shape, and domain. A property answers "what state is it in?" — mutable lifecycle. State-as-tag conflates the two: a `draft` or `closed` tag churns the identity axis when lifecycle moves, so a closed `todo` would fall out of `where({"tagged": "todo"})`. State lives in `document.status`, `document.priority`, and the like; the tag set stays fixed. The full principle, the type/shape/domain taxonomy, and the practical cases are in [[docs/notes/tags-classify-properties-carry-state.md]].

## Edge stereotypes are open-vocab labels on mentions edges

An `edge.<stereotype>: [paths]` entry materializes one `mentions` edge per path plus a stereotype row in `edge_property` — open-vocabulary labels (`supports`, `contradicts`, `supersedes`) classifying what kind of mention an edge is, without extending the closed edge-kind enum. A new stereotype is a doc-and-parser change, never a schema migration, exactly as tags work; the parser does not warn on unknown values, and vocabulary earns canonical status by use. The full model, the inline-versus-frontmatter authoring surfaces, and the seed vocabulary live in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].

## Obsidian and Dataview compatibility

Hoplite shares its corpus with Obsidian and Dataview, and the frontmatter shape is chosen to stay readable by both. A corpus file opens and renders in Obsidian unchanged — body `[[wikilinks]]` resolve as native links, and every frontmatter key appears in Obsidian's Properties panel. Dataview reads arbitrary frontmatter fields, including the dotted and nested `document.` and `edge.` forms, so a query can filter on `document.status` or list `document.tags` directly.

The class-prefix namespace makes one deliberate concession. Obsidian's native tag features — the tag pane and `tag:` search — key on a bare top-level `tags:`, so `document.tags` reads there as an ordinary property, not a native tag; Dataview and the Properties panel see it either way. Namespacing tags under `document.` is the chosen trade: node-property versus edge-stereotype disambiguation over Obsidian's built-in tag UI.

## Malformed frontmatter: fatal versus soft

The parser splits failures by blast radius.

Fatal failures drop the document from the graph with a warning, because its core identity is unusable: missing frontmatter, unparseable YAML, a non-mapping block, a missing mandatory field, or a non-list `document.tags` / `document.aliases`.

Soft failures keep the document, drop the offending fragment, and warn: a null list element (a dangling `-`), an empty `document.tags` or `document.aliases` (omit the key instead), or a non-list `edge.<stereotype>` (a scalar where a path list belongs). A malformed annotation should not cost the whole file the way a missing `title` does. Both warnings surface in `WriteResult.warnings`, so the agent is notified while the file is still indexed. The implementation is `plugins/hoplite/mcp/src/hoplite/frontmatter.py`.

## Tradeoffs and open possibilities

- EAV decomposition. List-valued properties fan out one row per element in `node_property`, and stereotypes likewise in `edge_property` — the same shape on both sides of the graph. It is uniform, queryable, and schema-free for new keys; the cost is that a property value is always text, so an authored `document.priority: 5` reads back as the string `"5"`.
- Open vocabulary. Neither tags nor stereotypes validate against a fixed set. The gain is zero-friction extension; the risk is synonym drift (`supports` versus `endorses`) with no audit affordance yet.
- Deferred. A shared component capturing the v1 state vocabulary (`document.status`, `document.priority`, `document.effort`) once more artifact types reuse it; edge-level properties beyond stereotype (which edge would `edge.tags` address?); a usage-histogram tool to catch stereotype drift before it accumulates. The two design notes carry the standing questions.

## The two derived artifacts

This note is the design source of truth. Two downstream artifacts derive from it and must not contradict it:

- `templates/components/shape/frontmatter.md` — the operational handbook, mail-merged into the four skills and the `check-frontmatter` hook. Sparse by intent: the rules an agent needs mid-task, none of the rationale above.
- `plugins/hoplite/mcp/src/hoplite/frontmatter.py` — the implementation: split, normalize, validate, and project into FTS fields, node properties, and edge stereotypes.

## See also

- [[docs/notes/tags-classify-properties-carry-state.md]] — identity versus state, in full.
- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — the edge-stereotype model, in full.
- [[docs/hoplite/hoplite-architecture.md]] — the system this envelope feeds.
