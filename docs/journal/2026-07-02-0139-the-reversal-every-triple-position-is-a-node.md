---
title: The reversal — every triple position is a node
summary: "Working the RDF alignment past the stereotype→predicate rename, the model reversed: documents aren't nodes, they bind to nodes; tags, property values, and out-of-line content get nodes too. Subject and object are always nodes, the middle is always a predicate. Property keys join the predicate vocabulary, flipping the day-old edges-only scope decision. Value nodes split into two addressing schemes: value-carrying uris (status/locked) and slot uris (summary/<doc-uri>), after surrogate ids and content hashes were each rejected."
tags: [journal, hoplite]
created: 2026-07-02
---

# The reversal — every triple position is a node

## Context going in

The RDF terminology alignment had just landed: `stereotype` retired into `predicate` (glossary, locked specs, schema.md, skills — 2026-07-01), the read-side `predicate` renamed to `condition`/`search-expression` to free the word, and the scope decision recorded as **edges only** — property keys keep `property`, matching OWL's `ObjectProperty`/`DatatypeProperty` split. The boundary note `hoplite-is-rdf-at-source-property-graph-at-index.md` argued the schema was a deliberate hybrid, "not collapsible to a single EAV table," with two triple families split by object type: edges (object = resource) and node properties (object = literal).

## What happened

Walking node properties through RDF (`status: locked` → `:doc :status "locked"`) surfaced the literal-vs-resource question. Tags broke it open: the schema *interns* tags into their own table and the namespace view addresses them (`node/tag/note`) — so `:doc :tag :note` with a resource object was already more faithful to storage than a literal. Mark then made the reversal explicit:

> "nodes are nodes. documents aren't nodes... anything that can be on the left is a node (maybe always documents), anything in the middle is a predicate (edge), anything that can be on the right is a node (both documents and property values)."

The locked glossary already licensed it — `node` is "identity, and nothing more... a node names a resource, it does not describe it," and `document` *has-a* node. The reversal overturns the schema's failure to believe the glossary, not the glossary.

Consequences accepted in the moment:

- Property keys become predicates — "RDF all the way," flipping the edges-only scope decision made **the previous day**. The `predicate`↔`property` contrast will need redrawing.
- Edge granularity changes: one row per `(src, predicate, dst)` statement instead of one per `(src, dst)` pair with a predicate set; `confidence` becomes per-statement.
- `tag`, `node_tag`, `property_key`, `node_property` dissolve into nodes + edges; the `namespace` view stops being a projection and becomes real nodes; survey literally becomes match + walk, as `one-walk-verb-spans-the-corpus-and-vocabulary-graphs.md` predicted.

## The addressing fight

Expected the hard part to be scalars and blobs (title, summary, minhash, created), and it was. Three schemes tried:

1. **Surrogate row id** (`summary/55`) — rejected on the corpus's own precedent: surrogate ids regenerate on every drop-and-recreate rebuild, so they cannot serve as addresses (the `edge.id` argument in the one-walk note). Fails *wrong*: after a rebuild a held reference silently returns someone else's content.
2. **Content hash** (`summary/a3f9…`) — proposed for stability, dedup, and verifiability (the git-blob model). Mark rejected it: the hash goes stale when the summary changes. Resolution of the disagreement: the hash names the *value*, not the *slot* — but the slot is what a citation wants.
3. **Slot address** (`summary/<document-uri>`) — Mark's solution, and the landing point: for functional predicates (one summary, one title, one minhash per document), subject + predicate determines the node, so the document's own uri is the address. Stable across edits, live content on dereference, rename hazard already covered by aliases.

The derivability insight fell out immediately: a slot node's address is computable from the triple's other two positions, so these triples carry no new information — storage keeps a keyed facet table and the graph layer *projects* the nodes, exactly the pattern in `uris-are-a-tool-layer-projection-over-relational-storage.md`.

Also settled in passing: `hoplite://` as a dereferenceable uri scheme (the IRI story without the semantic-web stack), `created` is an ordinary property (value node `created/2026-06-30`, range queries ride lexicographic ISO-8601 uri scans), repeated triples give set semantics that match `node_tag`'s dedup exactly (and expose "key/bag" in older notes as a misnomer — it's key/set).

## What this cost

The boundary note's "why not one EAV table" argument mostly dissolved — its objections (walk indexes, confidence's home, object domains) are all answered by interned predicates, per-statement confidence, and the two addressing schemes. A day-old locked contrast (`predicate`↔`property`) is back on the table. Glossary changes wait: the read-side cluster's lock pass is deliberately held for Mark's review, and this reversal now queues behind it.

Current state lives in [[docs/notes/every-triple-position-is-a-node.md]].
