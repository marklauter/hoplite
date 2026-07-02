---
title: Every triple position is a node
summary: "The graph is triples over a node dictionary. Subject and object are always nodes — documents bind to nodes, and tags, property values, and out-of-line content get nodes too; the middle is always a predicate, and property keys are predicates. Value nodes come in two addressing schemes: value-carrying uris for categorical values, slot uris for functional per-document content. Slot nodes are derivable, so the document facet dissolves into a generic slot store projected into the graph."
tags: [note, hoplite, graph, schema, design]
created: 2026-07-02
status: evolving
---

# Every triple position is a node

The graph is triples: `subject — predicate — object`. Subject and object are always [[docs/hoplite/glossary/node.md|nodes]]; the middle is always a [[docs/hoplite/glossary/predicate.md|predicate]]. A [[docs/hoplite/glossary/document.md|document]] is not a node — it binds to one (the locked glossary already says so: a node is "identity, and nothing more"). Tags, property values, and out-of-line content bind to nodes the same way.

```
:docs/notes/foo.md  :cites    :docs/notes/bar.md      # document → document
:docs/notes/foo.md  :tag      :tag/note               # document → shared value node
:docs/notes/foo.md  :status   :status/locked          # document → shared value node
:docs/notes/foo.md  :created  :created/2026-06-30     # document → shared value node
:docs/notes/foo.md  :summary  :summary/docs/notes/foo.md   # document → slot node
```

## Predicates unify

Property keys are predicates. `status`, `tags`, `created`, `summary` sit in the same open vocabulary as `cites` and `supersedes` — the middle position is one kind of thing. This supersedes the edges-only scope choice recorded in [[docs/notes/edge-predicates-are-glossary-governed.md]] (its governance is unchanged; every predicate goes through the glossary reduction). The `predicate`↔`property` glossary contrast needs redrawing — held for the read-side lock pass.

## Two addressing schemes for value nodes

### Shared value node

- Address: the value itself — `status/locked`, `tag/note`, `created/2026-06-30`.
- Carries: categorical, multi-document, slug-safe values.
- One node per distinct value, shared by every subject that asserts it — which is what makes values walkable ("who else carries this value").
- Range queries ride lexicographic uri scans; ISO-8601 dates sort.

### Slot node

- Address: the subject's uri — `summary/<doc-uri>`, `title/<doc-uri>`, `minhash/<doc-uri>`.
- Carries: functional predicates — one value per document — whose content is freeform text or a blob.
- A stable citation with live content; dereference returns the current value.
- The rename hazard is covered by the existing alias machinery.

The line is *slug-safe and enumerable → the value is the address; freeform or binary → the slot is the address*. Surrogate row ids are ruled out as addresses (they regenerate on rebuild — the `edge.id` precedent in [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]]). Content hashes were considered and rejected for slots: a hash names a value, but a citation wants the slot's current content; snapshot-of-record already lives in git history.

## Slot nodes are projections

A slot node's address is computable from subject + predicate, so its triple carries no new information. Storage keeps a generic slot store — `slot(nodeid, predicateid, value)`, the long-value half of the term dictionary — and the graph layer projects the nodes on demand: the pattern in [[docs/notes/uris-are-a-tool-layer-projection-over-relational-storage.md]]. The document facet dissolves into it: `title`, `summary`, and fingerprints are slot rows, not columns, so a new slot predicate is data, never a migration. The model is uniformly triples; the physics stays a keyed lookup where a keyed lookup wins.

## Consequences for the schema

- `edge` becomes one row per statement `(src, predicate, dst)` — not one per `(src, dst)` pair with a predicate set — and `confidence` is per-statement.
- `tag`, `node_tag`, `property_key`, `node_property` dissolve into nodes + edges; `document` dissolves into the slot store, with `content_hash`'s slot row as the document/ghost witness.
- The `namespace` view stops being a projection: vocabulary entries are real nodes. Survey is literally match + walk over them.
- Addresses are bare uris; the MCP tool layer is the resolver, taking them as parameters. No uri scheme — that would be API packaging in the model (if graph entities are ever exposed as MCP resources, a scheme becomes a wire-format detail of the tool api). The vault segment remains the growth path to cross-repo identity.
- Multi-valued properties are sets (repeated triples; asserting twice yields one triple) — older notes saying "key/bag" mean key/set.

The schema realizes this model: [[docs/hoplite/schema.md]] (node, predicate, edge, slot, plus aliases and FTS).

## Supersedes

- [[docs/notes/hoplite-is-rdf-at-source-property-graph-at-index.md]] — its two-family split (edge = resource object, property = literal object) and its "why not one EAV table" argument predate this model; the objections are answered by interned predicates, per-statement confidence, and the two addressing schemes. Revise it against this note.

How this settled: [[docs/journal/2026-07-02-0139-the-reversal-every-triple-position-is-a-node.md]].
