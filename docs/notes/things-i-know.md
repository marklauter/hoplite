---
title: things I know
summary: assertions on the code base
tags: [note, hoplite, architecture, refactor]
created: 2026-05-28
document:
  status: design
---

# things I know

author's act → reader's payoff

asserstions on the code base

judgment-under-uncertainty

## ready to ship

- schema.sql


## problem statement
 `grep` is a loan shark.

A knowledge graph cuts waste by locating relevant content without reading for it. Debt avoided, not debt repaid. 

 
- You go to the catalog with keys you already hold — a subject, a title, a Dewey number, a term. You get back exactly what matches what you asked.
  - This is closed-loop. → search.
- But you leave the loop richer: the bibliography hands you titles you didn't have, and "along the way my vocabulary grows — I discover related terms that require additional searches." You got back things you didn't know to ask for. 
  - This is open-loop. → discover.
- Search spends the frontier; discovery expands it.



## scratch

1. Feature layer — where a document's facts come from. Two origins:
  - intrinsic — falls out of what the document is: uri/identity, creation time, content fingerprint. Emitted, not authored.
  - asserted — the author writes it down: title, summary, tags, properties, stereotypes, and the wikilinks themselves.
2. Edge layer — where a relationship comes from. Two provenances (your locked binary):
  - declared — the author asserted the relationship itself (a wikilink, a stereotype).
  Confidence 1.0.
  - discovered — the engine inferred the relationship from shared features. Graded.

-----

1. The foundation the vision should plant, at altitude, so downstream has ground to stand on:
   - document carries features — some intrinsic (emitted), some asserted (authored)
   - documents connect by relationships — some declared (authored directly), some discovered (inferred from shared features)
   - the link between them: discovery is inference over shared features — the engine reads the features the author never meant as relational and crystallizes the relationships they imply
   - meaning is the precipitate (your line-98 reframe — Hoplite is a signal What falls out: two layers, two axes, and inference as the bridge)

2. Everything in the scratch sorts cleanly once you separate the feature layer from the edge layer:
   - Feature layer — where a document's facts come from. Two origins:
     - intrinsic — falls out of what the document is: uri/identity, creation time, content fingerprint. Emitted, not authored.
     - asserted — the author writes it down: title, summary, tags, properties, stereotypes, and the wikilinks themselves.

3. Edge layer — where a relationship comes from. Two provenances (your locked binary):
  - declared — the author asserted the relationship itself (a wikilink, a stereotype). Confidence 1.0.
  - discovered — the engine inferred the relationship from shared features. Graded.

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

edges: Declared · Described · Discovered
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




3. The tree is the wrong tool for an ontology — a directory gives each file one home, though the idea belongs in many.
   - directory hierarchy doesn't match real-world relationships between concepts
   - a concept that matters in many places is filed in one folder; hierarchy forces a single home
4. Connection is invisible — even what the tree holds, it can't connect from glob-grep alone.
   - relationships between documents are invisible — the links you drew, the kinship of shared tags, the similarity no one wrote down; the filesystem shows containment, never connection
   - a document shows what it points to, never who points back; the filesystem has no inbound view
   - references to not-yet-written documents vanish — the backlog of intended work goes invisible, with no ghost to mark it


old solution statement: 

Mapping the corpus — its explicit, semantic, and emergent relationships, and the meta descriptions on each document — creates new affordances. The agent walks the corpus progressively, reading only what bears on the task. The result is less wasted context, less bias from stray input, and the agent kept in its smart-zone.

### Declare and describe — applying explicit structure

Explicit structure is asserted, not derived — the author supplies what the bytes can't yield: a relationship that lives only in the link, a title that isn't the filename, a summary the document doesn't contain.

1. Declare a relationship — point one document at another.
   - a `[[wikilink]]` declares an explicit relationship — the edge grep can't see
   - a markdown link declares too — a reference to a URL is an edge to content outside the corpus, not only doc-to-doc; the corpus's reach doesn't stop at its own files
   - declared once, it reads both ways — the backlink (inbound edge), who points here, is free structure
   - direction follows the stereotype: the arrow always has a tail and a head, so the backlink is always there, but whether the tie is symmetric is the stereotype's call — `supersedes` runs one way, a `related` or `not-related` tie reads both
   - a ghost link declares an open loop — aspirational, not-yet-written content made explicit rather than lost
2. Describe a document or an edge — annotate the structure.
   - a title and summary are asserted, not extracted — a filename is not a title, and a document carries no summary of itself; the author supplies both
   - the summary is the lede — the asserted gist an agent reads to decide whether to open the document or follow the edge
   - properties classify and qualify a document (tags, status) and crosscut the folder it's filed in
   - a stereotype on a link says what kind of relationship it is: cites, supports, supersedes, contradicts
   - describe an edge once and the stereotype rides it — inline next to the claim it makes, or in frontmatter as a document-level fact; same structure either way, the author picks rhetorical-in-context vs. categorical
   - the vocabulary is open — tags and stereotypes aren't a fixed menu; the author coins a label and it earns canonical status by use, the way tags already do

### Discover — inferring latent, emergent structure

The corpus holds undiscovered relationships — implicit kinship that emerges from shared features: topics, tags, citations, commits, authors, proximity of time and space. A declared relationship is asserted and treated as fact. A latent signal is implied — present only as a pattern, recovered by inference.

Every inferred relationship is graded by the improbability of the coincidence — a rare shared feature, or a narrow shared window. Two documents sharing a common word carry zero signal; two sharing a rare term carry a strong signal. That's why relationships derived from latent signals can be ranked.

Signals resolve into three channels, each an independent feature space:

1. Content and metadata — lexical and topical similarity, shared classification, temporal proximity.
   - topical kinship — two documents about the same thing with no link between them; similarity surfaces the relationship the author missed, and at the high-similarity extreme the same signal gathers a set of near-duplicates into one neighborhood instead of leaving them as N strangers
   - classification kinship — documents sharing a tag relate by kind even when their topics diverge
   - arcs — documents created close in time tend to share the intent of whatever was underway; the design arc (genesis → build → refactor) is one shape, every activity traces its own; never declared, it falls out of time
2. Structure — topology, not content: a rare connector couples strongly, a hub weakly.
   - co-citation — two documents pointed to by the same third
   - bibliographic coupling — two documents that point to the same third
   - shared citation — two documents that cite the same external source
   - entity co-mention — two documents naming the same rare entity (a file, an identifier, a ticket); the mention reifies the entity as a node, so a shared one couples the documents through it, the way a shared citation does — but recovered from prose, not a declared link
   - hubs — a node's centrality, not a pairwise tie: a document many point to is central to the corpus, and as a shared connector it couples weakly
3. History — provenance from the commit graph: co-change, co-authorship, shared lineage.
   - change coupling — documents changed in the same commit, often a stronger signal than content
   - co-modification — edited in the same session
   - same author

The tradeoff — latent signal buys recall at the cost of precision: it finds the connection the author missed, and sometimes one that isn't there; the threshold is the knob.

Provenance ranks above score: every discovered tie is graded, but a declared edge carries full confidence and outranks any discovered one for the same pair. The author's word beats the engine's guess, so the reader establishes trust per edge by where it came from.

### Read — navigating mapped relationships

Affordances emerge from the mapped structure: survey the vocabulary, filter by meaning, walk relationships, project and read the results.

1. Survey — retrieve the schema vocabulary, properties and stereotypes, before composing a predicate over the corpus.
2. Filter — narrow the corpus to the subset a Boolean predicate admits (`note & mcp & !draft`): semantic search matches by meaning, not literal string or path; properties crosscut folders, so filtering by one gathers a concept wherever it lives.
3. Walk — traverse declared and discovered edges from a node to gather a neighborhood the tree can't show: a relationship declared once reads both ways (inbound and outbound edges); ghosts keep open loops enumerable.
4. Project — organize the resultset: sort it by score or distance, shape what each hit returns (the lede and tags, never the body), and cap the hops and result set size. Hoplite hands back a projection, not a document — so the agent judges relevance from the summary authored in [Describe](#declare-and-describe--applying-explicit-structure) before spending a token to open the file.
5. Read — the built-in Read tool. Hoplite ends at the projection; the agent crosses to full content only for the hits that survive.


  The mirror, so you can see the seams (each solution closer retires its problem
  closer):

  - Para 1 (tax) — "reads the lede, not the leaf" answers P1's "every hit is a raw
  leaf"; "opens only what pays" retires "every wasted read is debt."
  - Para 2 (blind) — "reaches what it never thought to name" answers P2's "matches
  only what the agent can name"; "Hard-won memory sits one hop away" flips P2's
  "Hard won memory sits unused" verbatim.
  - Para 3 (lost) — "the reward for every leaf read and every dead end ruled out
  is kept, not discarded" is P3's exact phrase with the fate reversed; "Knowledge
  compounds" inverts "Knowledge that compounds is lost."
  - Para 0 mirrors problem para 0: where the problem defined useful → relevant →
  locate and consume, the solution defines the map → query → a choice, ending on
  the same two verbs ("locating and consuming") it set up.

  Two accuracy calls I made deliberately, flagging so you can veto:

  1. I did not claim synonym/semantic reach (e.g. "search 'cache,' get the
  'memoization' note"). Your matching is BM25/FTS + minhash — lexical, not
  embeddings — so it can't bridge synonyms. The honest "reach what you can't name"
  is discovery by traversal (open-loop: walk to neighbors you never queried), not
  magic search. Para 2 is built on that, which is both true and the more
  distinctive claim.
  2. Para 0 says "ranks what matches" rather than "matches by meaning," for the
  same reason — kept it to what FTS ranking actually does.

  Where do you want to push? My own least-favorite line is para 1's "The
  exploration loop collapses to a query and a few deliberate reads" — it's a touch
  flat next to the others. The rest I'm fairly happy with, but it's your voice
  the doc has to sound like.



  ### Declare and describe — applying explicit structure
  
  The author asserts what the bytes can't yield: a relationship that lives only in a link, a title that isn't the filename, a summary the document never states. This is explicit structure — supplied, not inferred — and the graph treats it as fact.
  
  A wikilink declares a relationship grep can't see: a directed edge from one document to another. A markdown link declares one too, reaching content outside the corpus — the graph's edges don't stop at its own files. Declared once, an edge reads both ways; the backlink, who points here, is free structure. Whether the tie is symmetric is the stereotype's call — `supersedes` runs one way, a `related` or `not-related` tie reads both. A ghost link declares an open loop: not-yet-written content made explicit rather than lost.
  
  Description annotates the structure. A title and summary are asserted, not extracted — a filename is not a title, and a document carries no summary of itself. The summary is the lede the agent reads to decide whether to open the document or follow the edge. Properties — tags, status — classify a document and crosscut the folder it is filed in. A stereotype labels an edge with the kind of relationship it carries: cites, supports, supersedes, contradicts. Describe an edge inline beside the claim it makes, or in frontmatter as a document-level fact — same structure either way. The vocabulary is open: the author coins a label and it earns canonical status by use, the way tags do.
  
  ### Discover — inferring latent, emergent structure
  
  Beyond what the author declared, the corpus holds relationships no one wrote down — implicit kinship that emerges from shared features. A declared edge is asserted and treated as fact; a latent signal is implied, present only as a pattern the engine recovers by inference.
  
  Every inferred relationship is graded by the improbability of the coincidence — a rare shared feature, or a narrow shared window. Two documents sharing a common word carry no signal; two sharing a rare term carry a strong one. That grading is why discovered relationships can be ranked.
  
  The signals resolve into three channels, each an independent feature space.
  
  Content and metadata measures what the documents mean. The content comparison is lexical today — shared vocabulary and overlapping phrases — surfacing a kinship the author missed and, at its extreme, gathering near-duplicates into one neighborhood instead of N strangers; but lexical overlap couples documents that share words and misses those that share meaning without them. Semantic comparison is the aspiration — coupling the caching note to the memoization note though they name nothing in common — and it lives as a ghost, [[ghost/semantic-similarity]], until the engine reads meaning from the prose rather than its surface. The metadata needs no such inference: a shared tag relates documents by kind even when their topics diverge, and documents created close in time share the intent of whatever was underway, tracing an arc — genesis, build, refactor — that no one declared and that falls out of time.
  
  Structure measures topology, not content: two documents pointed to by the same third, pointing to the same third, citing the same external source, or naming the same rare entity couple through the shared connector — a rare connector strongly, a hub weakly. History measures provenance from the commit graph: documents changed in the same commit couple, often more strongly than their content suggests, as do documents edited in the same session or by the same author.
  
  Latent signal buys recall at the cost of precision — it finds the connection the author missed, and sometimes one that isn't there. The threshold is the knob. Provenance ranks above score: every discovered tie is graded, but a declared edge carries full confidence and outranks any discovered one for the same pair. The author's word beats the engine's guess.
  
  ### Read — navigating mapped relationships
  
  Affordances emerge from the mapped structure: survey the vocabulary, filter by meaning, walk relationships, project and read the results.
  
  1. Survey — retrieve the schema vocabulary, properties and stereotypes, before composing a predicate over the corpus.
  2. Filter — narrow the corpus to the subset a Boolean predicate admits (`note & mcp & !draft`): semantic search matches by meaning, not literal string or path; properties crosscut folders, so filtering by one gathers a concept wherever it lives.
  3. Walk — traverse declared and discovered edges from a node to gather a neighborhood the tree can't show: a relationship declared once reads both ways (inbound and outbound edges); ghosts keep open loops enumerable.
  4. Project — organize the resultset: sort it by score or distance, shape what each hit returns (the lede and tags, never the body), and cap the hops and result set size. Hoplite hands back a projection, not a document — so the agent judges relevance from the summary authored in [Describe](#declare-and-describe--applying-explicit-structure) before spending a token to open the file.
  5. Read — the built-in Read tool. Hoplite ends at the projection; the agent crosses to full content only for the hits that survive.
  


  ❯ i have an idea about ranked hits. it came from rarity. two docs share a rare    
  tag, high rank. two docs share common tag (note), low rank. but proximity       
  matters too, so docs in the hoplite folder are likely related. two docs sharing 
  features across dimensions should rank high. this is like jackard ranking, but  
  over features. tags, properties, property values, stereotypes, graph            
  neighborhood, etc.                                                              
  
● Yes — and you've just derived the mechanism behind your own glossary stub. Line
  74: "inferred — semantic similarity (weighted minhash), weighted aggregation of 
  intrinsic and asserted features." That's exactly this. You wrote the conclusion;
  now you've got the construction.

  What it is, named: weighted Jaccard over a unified feature set, where each
  feature is weighted by its rarity (IDF). That's the whole idea, and it's
  principled.

  The construction. Represent each document as a set of feature tokens drawn from
  every dimension:

  docA → { tag:note, tag:minhash, prop:status=design,
           stereotype:supersedes→docX, neighbor:docY,
           folder:docs/hoplite, created:2026-06 }

  Weight each token by rarity — idf(f) = log(N / df(f)), df = how many docs carry
  it. Then similarity is the rarity-weighted overlap of two docs' token sets.
  Sharing tag:note (everyone has it, df huge) contributes ~nothing; sharing
  tag:minhash or a rare entity:co-mention (df = 2) contributes a lot. And because
  all dimensions live in one set, sharing across dimensions accumulates
  automatically — that's the "high rank for multi-dimensional overlap" you want,
  with no special combination rule. It falls out of the union.

  This is the same principle you already wrote, generalized. The Discover section
  says discovery is "graded by the improbability of the coincidence — a rare
  shared feature, or a narrow shared window." Improbability of coincidence is IDF:
  two random docs both carrying a feature of frequency p collide with probability
  ~p², so rare features are high-signal. Your idea is just: apply that grading to
  every feature dimension and sum, instead of only to text shingles. The current
  minhash-over-shingles is then one special case — shingles are simply the content
  dimension's features.

  It also collapses your "three channels" into one space — elegantly. Structural
  coupling stops being a separate mechanism: co-citation is a shared neighbor:
  feature; bibliographic coupling is a shared out-neighbor; entity co-mention is a
  shared entity: feature. Topology becomes feature-membership. So "content /
  structure / history" stop being three independent similarity computations and
  become three groups of features in one weighted-Jaccard. Cleaner model — though
  see the wrinkle.

  The one wrinkle — discrete vs. continuous. Jaccard is set-membership; it nails
  "rare shared feature" but not "narrow shared window." Time and space are
  continuous — two docs created 3 minutes apart aren't a set-membership match,
  they're close. To fold proximity into the feature set you have to bin it
  (created:2026-06, created:2026-06-07), and binning is lossy at the boundary
  (23:59 vs 00:01 land in different buckets). So either bin proximity into
  features (fits the unified model, loses sharpness) or keep proximity as a
  separate distance kernel multiplied in (sharper, breaks the single-Jaccard
  elegance). Your "rare shared feature / narrow shared window" phrasing already
  names both modes — this is just where they diverge mechanically.

  Implementation angle, since it rides on the existing schema. You don't need
  minhash for the structured features at all. Per-doc structured feature sets are
  small (dozens of tokens), so an inverted index — feature → posting list of docs,
  each posting carrying the IDF weight — lets you compute exact weighted overlap
  cheaply: node_property already gives you tag/property features, edge gives you
  neighbor features. MinHash earns its keep only on the content dimension, where
  shingle sets are huge and you need the sketch. So the honest split is: content →
  minhash sketch; structured features → exact weighted Jaccard over an inverted
  index. Two mechanisms, one combined score. No schema change — it's all derivable
  from the tables you have.

  The design question for the doc: does this reframe Discover from "three
  independent feature spaces" into "one weighted-feature similarity, the channels
  as feature groups"? That's truer to where you're headed and matches the stub —
  but it's a real rewrite of that section's framing, so I'd hold it until you
  decide. Want me to sketch what the Discover prose looks like under the
  unified-feature framing, so you can compare it side-by-side with the current
  three-channel version before committing?



  ## Signifiers — the cue that makes an affordance perceivable

A signifier is the perceptible cue that advertises an affordance. Read affordances signify through MCP tool descriptions; write affordances signify through ambient info-injection skills. The signifier carries a fidelity contract — it must advertise the affordance the mechanism actually offers, no more — and the build-time mail-merge keeps the two in sync, so a description never promises a move the mechanism does not make. A signifier the agent cannot perceive leaves the affordance dead, which is why the signifiers stay implicit in the surfaces the agent already reads rather than living as a separate layer.
