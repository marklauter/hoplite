---
title: Maps of meaning - information search, discovery, and retrieval
summary: Reading is an expensive operation. Indexes reduce the cost.
tags: [hoplite, overview, spec]
created: 2026-05-30
---

# Maps of meaning - information search, discovery, and retrieval

maximizing signal to noise

Reading is the expensive operation indexes exist to avoid.

Search spends the frontier; discovery expands it.

An agent works within a fixed context budget. It must act on a corpus larger than it can read. The agent has a limited set of built-in tools: glob, grep, and read. It can discover relationships with these tools, but it burns tokens, relies on error-prone judgement, and injects bias by reading off-task content. 

The default tools operate over surface text, recovering only content channels — lexical and topical overlap, a shared rare term. Relatedness carried by graph topology, by commit and authorship provenance, by temporal proximity is inexpensive to recover but unreachable: no graph exists to traverse, no history to read. These channels are recoverable after the corpus is reified as a graph.

Hoplite augments the default navigation tools through a map over the markdown corpus. Instead of relying on the agent to read, comprehend, and infer relationships on-the-fly, Hoplite applies structure to the markdown and reifies the map as a durable graph with declared and latent relationships. The agent navigates the map and reads selectively, spending its context on the subset that matters.

## The compounding cost of the grep-read-judge loop

For an LLM-based agent, knowledge that sharpens the context is useful. Content that contains useful knowledge is relevant. To acquire useful knowledge, the agent must first locate and consume relevant content.

The agent's default method of exploration, `grep`, is a primitive search tool that returns unranked and unordered results. The agent must sift through hits, loading each into the context and judging usefulness for itself. The exploration loop taxes scarce resources: time, tokens, turns, context budget, and bias-inducing attention. The quantitative and qualitative costs compound. Every wasted read is debt serviced for the life of the context.

Scanned noise biases the agent; so does signal it never reaches. `grep` matches only what the agent can name. Explore agents, guarding their context budget, scan excerpts and risk missing critical information. Hard won memory sits unused. The knowledge-starved agent exercises poor judgment: it reopens settled decisions, contradicts conventions, overwrites working code, and reproduces prior art. Failures compound.

The relationships the agent discovers are the reward for every leaf it read and every dead end it ruled out. They live in the context window and nowhere else. They die with the session. The next agent re-derives them from scratch, or not. Cost compounds. Failure compounds. Knowledge that compounds is lost.

## The solution — mapping the corpus; declare, describe, discover, and read relationships

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
