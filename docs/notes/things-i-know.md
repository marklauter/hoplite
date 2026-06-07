---
title: things I know
summary: assertions on the code base
tags: [note, hoplite, architecture, refactor]
created: 2026-05-28
document:
  status: design
---

# things I know

asserstions on the code base

- Reading is the expensive operation indexes exist to avoid.
- Reading is an expensive operation. Indexes reduce the cost.
- search/locate reduce the scanable surface. scan is consumes content linearly.

judgment-under-uncertainty

Relationships discovered die with the session...
re-derives a relationship


## problem statement
 `grep` is a loan shark.

A knowledge graph cuts waste by locating relevant content without reading for it. Debt avoided, not debt repaid. 

The graph is the invesment broker to .
 
- You go to the catalog with keys you already hold — a subject, a title, a Dewey number, a term. You get back exactly what matches what you asked.
  - This is closed-loop. → search.
- But you leave the loop richer: the bibliography hands you titles you didn't have, and "along the way my vocabulary grows — I discover related terms that require additional searches." You got back things you didn't know to ask for. 
  - This is open-loop. → discover.
- Search spends the frontier; discovery expands it.

## ready to ship

- schema.sql
- hoplite.md
- migrations.py
- db.py

## wip

## graph.py

## frontmatter.py

- created
- extracted from walker which lived in graph.py
- unreviewed
- frontmatter is an expression of the spec - the spec should be defined elsewhere

## hoplite-frontmatter.md
- created
- unreviewd

## hoplite-graph.md
- created
- unreviewd

Authored vs emergent
authored link graph via [[wikilinks]]
semantic graph - good

  So here's the recut I'd offer. Not "three graphs" — three sources of order over one node set, each a
  stronger claim than the last:

i now realized that d, d, and d are properties of edges: declared (wikilinks), described (property graph), discovered (inferred) due to semantic proximity

  1. Declared order — authored links (mentions, cites). The structure you wrote by hand.
  2. Described order — properties (tags, document.<key>). The facts you classified.
  3. Discovered order — semantic similarity (related). The adjacency the graph found that you never stated.

^ intrinsic / asserted / inferred is much better map than declared, describted, discovered because declared and described are really the same thing.

Declared · Described · Discovered
  - Declared — the author wrote the relationship. A wikilink, a stereotype. Zero inference; the edge is
  the authored thing.
  - Described — the author wrote a value about the node. Tags, dates, status. The relationship among
  co-described nodes is projected — equality for tags, proximity for dates. Explicit input, inferred
  edge.
  - Latent — the author wrote nothing relational, only prose. The detector reads the bytes and surfaces
  adjacency. Maximum inference.

  Hold "signal" — it's the right primitive, and it just demoted everything above it. You didn't reframe
  the words; you reframed the artifact. The knowledge graph isn't the thing you're building — it's the
  precipitate. What you're building is the detector, and the graph is what crystallizes once signals are
  found. That's why "order from chaos" finally fits without strain: chaos is noise, order is signal, and
  the whole machine is a signal-to-relationship transducer. The graph is the readout, not the goal.


  ---

    But here's the crack — same shape as the measurement-scale one. "Intentional / latent"
  is a crossed pair. They're not two ends of one axis; they're two different axes:

  - Intentional ↔ incidental — did the author mean to assert this? (about will)
  - Explicit ↔ latent — is the relationship stated, or must it be inferred? (about
  observability)

  Your own date insight is what splits them. A created date is intentional at the value
  (you wrote the date on purpose) but latent at the relationship (you never meant to
  assert "these two share an arc" — the arc emerges). So intent and latency come apart.
  The author explicitly states a value; whether that value implies a relationship is a
  separate question the detector answers.

    Which tells you what the graph actually cares about. Not the author's will — the edge's provenance:
  was the relationship declared or detected?

  - explicit / declared — the author authored the edge itself: a [[wikilink]], an edge.supports. The
  relationship is stated.
  - latent / detected — the edge is inferred from shared or proximate values, authored or extracted: tag
  co-membership, date proximity, shingle similarity. The relationship was never stated; the detector
  found it.

    One consequence to brace for: under this framing, a tag stops being "described order" and becomes a
  latent signal too — note+note is a detected co-membership edge, not a declared one. The only explicit
  signals left are wikilinks and edge stereotypes — the relationships you wrote as relationships.
  Everything else, tags included, is latent. Does that sit right, or does authoring a tag feel explicit
  enough to you that you want a middle term?

  Signal
  - Physics: a propagating disturbance carrying energy from a source to a receiver — a perturbation in a medium that varies in time or space.
  - Information theory: the part of a transmission that reduces the receiver's uncertainty; everything in the channel that isn't noise.
  - Semiotics: a sign whose meaning is fixed by convention or causation — it stands for something to someone.
  - Biology: a molecule or stimulus that triggers a response in a cell or organism; the input to a transduction pathway.
  - Economics: a costly, observable action taken to convey private information credibly (Spence's degree, the peacock's tail).
  - Software: an asynchronous notification — an event raised to interrupt, wake, or inform a process.


  So here's the agent's verb list — each verb, and the problem it hits with only files + grep:

  - Find — "what in the corpus bears on this task?" The agent has a topic or a class, not a filename. It
  needs a ranked, summarized shortlist so it can decide what to open without opening everything. Grep
  is literal (greps cache, misses memoization), unranked, and returns lines, not documents with
  summaries. → the agent can't locate relevant prior art cheaply.
  - Walk — "given this document, what connects to it?" Authored links the agent should follow, and
  similar documents nobody linked. Grep can find a [[wikilink]] string but can't follow a neighborhood,
  and it has no notion of similarity at all. → the agent sees one document and is blind to its context.
  - Scope — "restrict to a kind." Review only note for drift against code; ignore journal because the
  arc can't drift. The directory is the only partition a filesystem offers, and classification crosscuts
  directories. → the agent can't narrow to the set that matters.
  - Triage — "what's the state, what's next?" backlogged → in-progress → closed. There's no way to query
  lifecycle across the corpus from the filesystem. → the agent can't answer "what should I pick up."
  - Surface gaps — "what's referenced but unwritten?" The ghost backlog. → the open loops are invisible.


  ▎ The graph is a substrate of primitives. Processes compose over it. Design the primitives; let the 
  ▎ processes fall out. A use case doesn't earn a feature — it tests whether the primitives were 
  ▎ sufficient.


  progressive disclosure — the agent selects only the content it needs, cutting token waste and the bias from unrelated content. the mechanisms beneath it:

- semantic search (BM25 via FTS) matches documents by topic, not literal text
- ranked hits carry summaries, so the agent judges from the lede what to read or follow next
- walk follows declared links and discovered similarity to gather a neighborhood the directory can't show
- predicate scoping narrows to a classification instead of a folder
- discovery surfaces latent signal — relationships nobody authored
- discovered similarity clusters near-duplicates into one neighborhood instead of N strangers
- directed edges walk both ways — `direction: in` reveals who references this document
- ghost nodes make the unwritten enumerable, so open loops stay visible
- find surfaces prior art by topic; walk reaches the decision's rationale before the agent repeats it
- tags crosscut folders — find by classification gathers a concept wherever it lives


old graph content

## The model

The graph has two element types — nodes and edges — and the description that hangs off each.

- A node is an addressable resource: a document in the corpus.
- An edge is a directed relationship from one node to another.
- A property is a typed key/value fact attached to a node.
- A stereotype is an open-vocabulary label attached to an edge.

Description never connects things, and edges never carry identity. A node's tags say what it is; an edge's stereotype says what kind of link it is. That split — structure in nodes and edges, description hanging off both — is the spine of the model. The description takes a different shape on each side: a node carries an open key/value property vocabulary, an edge carries a set of stereotype labels. The symmetry is that both are described; it is not that they are described identically.

## Nodes

A node is identified by its `uri`: a medium-agnostic, case-insensitive locator. For a corpus document the uri is its repo-relative path (`docs/notes/foo.md`); `[[Docs/Foo.md]]` and `[[docs/foo.md]]` reach the same node because the uri collates case-insensitively.

Three node variants, distinguished by whether the uri resolves to a real resource:

- Document node — a real `.md` file on disk. `resolved = true`. Carries content fingerprints: an exact hash for change detection and a similarity sketch for near-duplicate detection.
- Ghost node — a wikilink target with no backing file, authored as `[[ghost/<slug>]]` for an intentional open loop. `resolved = false`, no content. A synthetic `ghost` tag makes the corpus's unwritten references enumerable.
- URL node — an external `http(s)` reference, keyed by the verbatim URL. `resolved = false`, terminal, a synthetic `url` tag.

## Edges

An edge is directed from `src` to `dst` and carries a `kind` and a `confidence`. Kind is a closed enum of two, and the two are *provenance* — who asserted the edge, not what it means:

- `declared` — the author asserted it, by writing a `[[wikilink]]` in body text. `confidence` is `1.0`.
- `discovered` — the engine inferred it from a shared or proximate feature (content similarity, co-citation, temporal proximity, and the rest). `confidence` is the graded strength of the inference.

Two things that look like kinds are not. A relationship's *meaning* — citation, refutation, endorsement — is an open-vocabulary stereotype on the edge, stored in `edge_stereotype`, never a new kind (see [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]]); a bare edge with no stereotype is simply a link. And the destination's *nature* — document, ghost, or URL — is a fact about the node, not the edge: a markdown link to an external site is a `declared` edge whose `dst` is a URL node, stereotyped `cites` only when the author means citation.

At most one edge connects a given ordered pair — `UNIQUE(src, dst)`, across both kinds. The two-pass build inserts `declared` edges first and `discovered` second, so a declared edge wins the slot over a discovered collision — declared beats discovered.

The enum is closed and stays closed; provenance is binary. Richer relationships are stereotypes, never kinds.

## Properties

Properties decompose entity-attribute-value: one row per (node, key, value). They are authored metadata on a document — `tags`, `status`, `created`, and the open vocabulary beyond. List-valued attributes fan out one row per element. Properties are a node affordance; an edge's description is its stereotype set (see [Edge stereotypes](#edge-stereotypes)), not a key/value bag.

The vocabulary is open — any property key is accepted and stored, with no schema change per new key — except for the reserved words below. Values are stored as text. `tags` values are casefolded for case-insensitive lookup; other values are stored verbatim.

The key vocabulary is interned: `property_key` is the corpus's property namespace made readable — the substrate Survey reads to hand an agent the keys it can filter on before it composes a predicate. A key is stored once and referenced by integer from every property row that carries it.

Surveying that vocabulary is the read graph's `match` shape turned on the schema — find and walk, the same two moves. Find reads the keys: a small list from `property_key`. Walk descends a key to its values — the distinct `value` rows under one `keyid`, served by the reverse index. The keys are the nodes of a vocabulary graph, `key → value` the edge, the values the reachable set. Whether a key carries a vocabulary or a free scalar resolves in the walk, never in a declaration: a key that reaches a handful of values is categorical — `tags`, `status`; one that reaches thousands of near-unique values is scalar — a timestamp, a score. Values need no interning of their own, and the schema needs no categorical flag; the `(keyid, value)` index carries the walk, and the agent reads the distinction off its result. The rule that falls out: intern the find namespace, not the walk values — `property_key` interns node keys, `stereotype` interns edge labels, while walk-reached node values stay inline. The edge side has a single description dimension and nothing beneath it, so its survey is the find alone — a direct read of the interned `stereotype` table, the edge-side counterpart to `property_key`, with no walk to follow.

Tags classify; properties carry state. A tag answers "what is this?" — immutable identity, the document's type and shape and domain. A mutable property answers "what state is it in?" Conflating them (a `draft` or `closed` tag) churns identity when lifecycle moves. The full principle is in [[docs/notes/tags-classify-properties-carry-state.md]].

## Edge stereotypes

A stereotype is an open-vocabulary label on a `declared` edge — `supports`, `contradicts`, `supersedes`, `not-related` — interned in `stereotype` and linked to its edges through `edge_stereotype`, classifying what kind of link the edge is without extending the closed kind enum. It is a label, not a key/value property: an edge's description is a set of stereotypes, not the open key/value vocabulary a node carries, so the labels live in their own interned vocabulary and a junction table rather than an EAV bag. That vocabulary is the edge-side survey namespace — the counterpart to `property_key`. A new stereotype is a vocabulary-and-parser change, never a schema migration, the same way tags work; the parser does not reject unknown values. The full model, the authoring surfaces, and the seed vocabulary are in [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]].

## Reserved words

Most property keys are open vocabulary. A few are reserved: keys with a defined meaning and validation across the graph, regardless of which surface authors them. A reserved word is specified here, in the model, not at the expression layer — frontmatter and wikilinks carry the value, this document says what it means and how it is validated.

- `created` — a creation timestamp. Prefers a full ISO date-time, and accepts a bare ISO date (`YYYY-MM-DD`) for backward compatibility with the corpus's authored dates. Optional; when absent, git history is the authoritative date.

The set is open and grows as keys earn defined semantics. Each reserved word names its type and validation rule here.

## Expressions of the graph

The model is authored and read through surfaces that map onto it:

- Frontmatter — node properties (`document.<key>`) and edge stereotypes (`edge.<stereotype>: [paths]`). The contract is [[docs/hoplite/hoplite-frontmatter.md]].
- Inline wikilinks — `[[docs/<path>.md]]` materializes a `declared` edge, `[[ghost/<slug>]]` an open loop, and `[text](https://…)` a `declared` edge to a URL node. The stereotyped form `[[stereotype:path]]` is designed but not yet wired.
- Queries — `where` (ranked FTS plus property filter) and `relatives` (edge traversal) read the graph back.

## Storage

The graph persists in SQLite. The tables, columns, indexes, and their rationale live in [`schema.sql`](../../plugins/hoplite/mcp/src/hoplite/schema.sql); this document does not restate the DDL. The mapping is direct: nodes to `node`, edges to `edge` (kinds interned in `edge_kind`), node properties to `node_property` (keys interned in `property_key`), edge stereotypes to `edge_stereotype` (labels interned in `stereotype`), the text projection to `fts`.

## Open questions

- Frontmatter doc retires into the express layer. [[docs/hoplite/hoplite-frontmatter.md]] still carries model content this canon now owns. Decided: dissolve it into [[docs/hoplite/hoplite-declare-and-describe.md]] as the frontmatter section — express-only, model deferred here — alongside inline wikilinks. Held until the access-pattern docs are authored; the doc stays frozen meanwhile.
- The reserved-word set is incomplete. Only `created` is named. Enumerate the rest and give each its type and validation rule, the way `created` has one.
- The implementation trails this canon. The parser, the handbook component, and the frontmatter hook still need to catch up to the model: drop `created` from the mandatory set everywhere it is still listed, and implement reserved-word validation (`created` as an ISO date-time that also accepts a bare ISO date). The model leads; the surfaces derive.

## See also

- [[docs/hoplite/hoplite-frontmatter.md]] — the frontmatter expression of this model.
- [[docs/notes/stereotypes-are-open-vocab-edge-properties.md]] — edge stereotypes in full.
- [[docs/notes/tags-classify-properties-carry-state.md]] — identity versus state.
- [[docs/hoplite/hoplite-architecture.md]] — the system around the graph.


## document structure

- hoplite
  - graph - describes structure: nodes, edges, property graph, stereotype graph, vocab, bm25 FTS, minhash ranked edges
    - discover
      - building minhash ranked edges
  - affordances
    - declare-and-describe (write-side affordances) - describes the complete mutation surface that is exposed through frontmatter and in-line content markers
      - frontmatter - extends declare and describe??? maybe absorbed into it
    - navigation (read-side affordances)
      - read-operations
        - survey vocabulary - array values, node properties, edge stereotypes
        - filter - property graph predicates, stereotype predicates
        - semantic search - FTS
        - walk - traversing the graph
        - projection - organizing result sets
      - tool-api - describes the mcp endpoint signatures

open question:

Good — file's unchanged, so I'm reviewing the version we built. Starting the deep pass
  top-down. Title/summary/intro are still your <todo> placeholders, so I'll skip those and
  start at the first structure section.

  Documents — review against schema.sql and the now-settled model:

  Accurate and complete against the node table — id, uri, resolved, content_hash, minhash,
  plus properties (node_property + property_key) and the first-class title/summary. Nothing
  missing, nothing wrong. The section is in good shape. Three things to weigh:

  1. Reserved words names only created (the carry-over item). Decide it as a decision, not a
  gap: either enumerate the rest with validation rules, or add one line — "the set is
  deliberately minimal for day one; created is the only reserved key" — so it reads
  intentional.
  2. The bullet list mixes registers — id/uri/resolved/content_hash/minhash are node columns;
  title/summary live in fts; properties spans two tables. We accepted this (it's the
  document's attributes, not node's columns) — flagging only because a schema-literal reader
  will notice. Leave as-is, I think.
  3. New-model touch: the Identity section describes uri bare (docs/notes/foo.md), which is
  correct for the stored form. The node/ namespace addressing we just worked out is the
  addressing-layer projection — it belongs in the note and the affordances/navigation doc, not
  here. So Documents stays bare-uri. The one optional add: a forward-pointer from Identity
  noting the uri is addressed as node/<uri> at the query layer. I lean omit — keep the
  structure doc free of addressing-layer concerns.

  So Documents needs only the reserved-words decision. Which way do you want it — enumerate,
  or declare-minimal? And once that's settled I'll move to Relationships (where the real items
  are: the overloaded Direction section, and the two-pass build that's really indexing
  behavior).