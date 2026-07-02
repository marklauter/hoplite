---
title: Every triple position is a node
summary: "The graph is triples over a node dictionary. Subject and object are always nodes — documents bind to nodes, and tags, property values, and out-of-line content get nodes too; the middle is always a predicate, and property keys are predicates. Value nodes come in two addressing schemes: value-carrying uris for categorical values, literal uris for functional per-document content. Literal nodes are derivable, so the document facet dissolves into a generic literal store projected into the graph."
tags: [note, hoplite, graph, schema, design]
created: 2026-07-02
status: evolving
---

# Every triple position is a node

The graph is triples: `subject — predicate — object`, and every position holds a [[docs/hoplite/glossary/node.md|node]]. The middle is special by *role*, not by kind: a [[docs/hoplite/glossary/predicate.md|predicate]] is a node carrying the predicate facet — the registration that licenses it for the middle position, so `doc-1 doc-2 doc-3` is unwritable — but as a node it stands as subject or object like any resource, so statements about the vocabulary are ordinary statements. A [[docs/hoplite/glossary/document.md|document]] is not a node — it binds to one (the locked glossary already says so: a node is "identity, and nothing more"). Tags, property values, predicates, and out-of-line content bind to nodes the same way.

Predicates were never ruled out of the dictionary — "not a node" was *edge's* property in the old model, and predicates inherited it by succession, not by argument, when they took over edge's core-concept role.

```turtle
:docs/notes/foo.md   :cites     :docs/notes/bar.md            # document → document
:docs/notes/foo.md   :tag       :tag:note                     # document → shared value node
:docs/notes/foo.md   :priority  :priority:high                # document → shared value node
:docs/notes/foo.md   :created   :created:2026-06-30           # document → shared value node
:docs/notes/foo.md   :summary   :summary:docs/notes/foo.md    # document → literal node
```

Two separators split two naming authorities: slash joins path segments (the filesystem's namespace), colon joins a predicate label to its operand (the vocabulary's namespace). The wikilink grammar forbids colons in targets, so the spaces are disjoint by construction — a vocabulary address can never collide with a document uri.

The sample is Hoplite's Turtle dialect. In Turtle-shaped contexts an address always appears namespace-qualified — the leading colon at minimum — never bare: Turtle's first colon is the namespace boundary (a prefix cannot contain one), so everything after it is the local name, where our separator colon is legal raw. The dialect relaxes strict `PN_LOCAL` in one way: raw `/` is allowed in local names — paths are just strings here; a strict-Turtle export escapes them (`\/`) or uses full-IRI form.

## Predicates unify

Property keys are predicates. `status`, `tags`, `created`, `summary` sit in the same open vocabulary as `cites` and `supersedes` — the middle position is one kind of thing. This supersedes the edges-only scope choice from the terminology alignment (see the journal entry below). The `predicate`↔`property` glossary contrast needs redrawing — held for the read-side lock pass.

## Two addressing schemes for value nodes

### Shared value node

- Address: the value itself — `priority:high`, `tag:note`, `created:2026-06-30`.
- Carries: categorical, multi-document values. The operand is a string; mid-token characters strict Turtle disallows (dots, dashes, slashes) ride the dialect relaxation, but whitespace is a token delimiter — how whitespace-bearing values address is an open question in [[docs/hoplite/schema.md]].
- One node per distinct value, shared by every subject that asserts it — which is what makes values walkable ("who else carries this value").
- Range queries ride lexicographic uri scans; ISO-8601 dates sort.

### Literal node

- Address: the subject's uri behind the predicate label — `summary:<doc-uri>`, `title:<doc-uri>`, `minhash:<doc-uri>`.
- Carries: functional predicates — one value per document — whose content is freeform text or a blob.
- A stable citation with live content; dereference returns the current value.
- The rename hazard is covered by the existing alias machinery.

The line is semantic, not lexical: *enumerable → the value is the address; freeform or binary → the subject is the address*. Surrogate row ids are ruled out as addresses (they regenerate on rebuild — the `edge.id` precedent in [[docs/notes/one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md]]). Content hashes were considered and rejected for literals: a hash names a value, but a citation wants the literal's current content; snapshot-of-record already lives in git history.

## Literal nodes are projections

A literal node's address is computable from subject + predicate, so its triple carries no new information. Storage keeps a generic literal store — `literal(predicateid, nodeid, value)`, keyed in address order, the long-value half of the term dictionary — and the graph layer projects the nodes on demand: the pattern in [[docs/notes/uris-are-a-tool-layer-projection-over-relational-storage.md]]. The document facet dissolves into it: `title`, `summary`, and fingerprints are literal rows, not columns, so a new literal-valued predicate is data, never a migration. The model is uniformly triples; the physics stays a keyed lookup where a keyed lookup wins.

## Consequences for the schema

- `edge` becomes one row per statement `(src, predicate, dst)` — not one per `(src, dst)` pair with a predicate set — and `confidence` is per-statement.
- `tag`, `node_tag`, `property_key`, `node_property` dissolve into nodes + edges; `document` dissolves into the literal store, with `content_hash`'s literal row as the document/ghost witness.
- `predicate` becomes a facet keyed by nodeid — a predicate is a node (`predicate:cites`) with a registration row, interned at first use in the middle position. The edge's middle column is typed to the facet, holding the role apart; the node identity makes predicates subjects and objects, so `cites inverse-of cited-by` is representable — stored like any triple, enforced by nothing.
- The `namespace` view stops being a projection: vocabulary entries are real nodes. Survey is literally match + walk over them.
- Addresses are bare uris; the MCP tool layer is the resolver, taking them as parameters. No uri scheme — that would be API packaging in the model (if graph entities are ever exposed as MCP resources, a scheme becomes a wire-format detail of the tool api). The vault segment remains the growth path to cross-repo identity.
- Multi-valued properties are sets (repeated triples; asserting twice yields one triple) — older notes saying "key/bag" mean key/set.
- The dictionary stores an address as `(namespace, local)`: a namespace table interns the roots — `document`, `url`, `predicate`, and one row per value-interned label — and the uri is a projection over the pair. No nullable columns: documents and urls belong to structural namespace rows.

The schema realizes this model: [[docs/hoplite/schema.md]] (node, predicate, edge, literal, plus aliases and FTS).

## Supersedes

- [[docs/notes/hoplite-is-rdf-at-source-property-graph-at-index.md]] — its two-family split (edge = resource object, property = literal object) and its "why not one EAV table" argument predate this model; the objections are answered by interned predicates, per-statement confidence, and the two addressing schemes. Revise it against this note.

How this settled: [[docs/journal/2026-07-02-0139-the-reversal-every-triple-position-is-a-node.md]].
