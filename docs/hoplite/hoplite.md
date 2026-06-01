---
title: Hoplite — Map your corpus; discover latent signals; protect context
summary: Hoplite is a knowledge graph over a markdown corpus, built for agents under a fixed context budget. It maps the structure an author declares and the latent signal an engine discovers, so the agent reads only the subset that matters instead of grepping and reading blind.
document:
  tags: [hoplite, overview, spec]
  created: 2026-05-30
---

# Hoplite — Map your corpus; discover latent signals; protect context

An agent works within a fixed context budget. It must act on a corpus larger than it can read. The agent has a limited set of built-in tools: glob, grep, and read. It can discover relationships with these tools, but it burns tokens, relies on error-prone judgement, and injects bias by reading off-task content. 

The default tools operate over surface text, recovering only content channels — lexical and topical overlap, a shared rare term. Relatedness carried by graph topology, by commit and authorship provenance, by temporal proximity is inexpensive to recover but unreachable: no graph exists to traverse, no history to read. These channels are recoverable after the corpus is reified as a graph.

Hoplite augments the default navigation tools through a map over the markdown corpus. Instead of relying on the agent to read, comprehend, and infer relationships on-the-fly, Hoplite applies structure to the markdown and reifies the map as a durable graph with declared and latent relationships. The agent navigates the map and reads selectively, spending its context on the subset that matters.

## The problem — glob-grep-read loop is the wrong tool for accessing a markdown corpus

The default toolset is simple and gets the job done most of the time. But the simplicity has a cost: exploring with the glob, grep, and read loop wastes turns, tokens, and attention. The agent has to re-derive the same relationships every session. `Explore` agents, in the interest of preserving the context budget, employ a grep excerpt loop that can miss relevant information. After exploring blind alleys, agents make decisions biased by the wrong content, or rehash decisions that were present in missed content. Failures compound.

1. Search matches the wrong way — an agent must find information that matters before it can use it.
   - grep finds direct text matches with regex, not semantic matches by topic
   - glob finds files by name, but the whole idea can't be contained in a name
   - matches are unranked and arrive unordered, so the agent can't tell what's central from what barely qualifies
2. Reading blind is costly — when search comes up wrong, the agent falls back to reading, and reading unranked and unfiltered costs twice.
   - reading unrelated files burns tokens for nothing
   - reading unrelated files injects bias into every future turn
3. The tree is the wrong tool for an ontology — a directory gives each file one home, though the idea belongs in many.
   - directory hierarchy doesn't match real-world relationships between concepts
   - a concept that matters in many places is filed in one folder; hierarchy forces a single home
4. Connection is invisible — even what the tree holds, it can't connect from glob-grep alone.
   - relationships between documents are invisible — the links you drew, the kinship of shared tags, the similarity no one wrote down; the filesystem shows containment, never connection
   - a document shows what it points to, never who points back; the filesystem has no inbound view
   - references to not-yet-written documents vanish — the backlog of intended work goes invisible, with no ghost to mark it
5. The corpus's memory goes unused — so the corpus repeats itself, the agent rewriting and rehashing what's already locked in.
   - the same idea gets rewritten across several notes; the agent reads redundant copies or never sees they converge
   - fixed context budget hides prior art — the agent can't find the decision already made
     - re-derive — re-solves a solved problem; wasted work, usually the same answer
     - contradict — lands on a different answer and breaks consistency; two conflicting decisions now drift apart

## The solution — mapping the corpus; declare, describe, discover, and read relationships

Mapping the corpus — its explicit, semantic, and emergent relationships, and the meta descriptions on each document — gives the agent new affordances. The agent walks the corpus progressively, reading only what bears on the task. The result is less wasted context, less bias from stray input, and the agent kept in its smart-zone.

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
