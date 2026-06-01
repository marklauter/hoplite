---
title: things I know
summary: assertions on the code base
document:
  tags: [note, hoplite, architecture, refactor]
  created: 2026-05-28
  status: design
---

# things I know

asserstions on the code base

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

  1. Declared order — authored links (mentions, cites). The structure you wrote by hand.
  2. Described order — properties (tags, document.<key>). The facts you classified.
  3. Discovered order — semantic similarity (related). The adjacency the graph found that you never stated.

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