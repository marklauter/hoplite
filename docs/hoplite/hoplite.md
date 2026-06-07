---
title: Maps of meaning - information search, discovery, and retrieval
summary: Reading is an expensive operation. Indexes reduce the cost.
tags: [hoplite, overview, spec]
created: 2026-05-30
---

# Maps of meaning - information search, discovery, and retrieval

maximizing signal to noise

Search spends the frontier; discovery expands it.

An LLM-based agent works within a fixed context budget. It must act on a corpus larger than it can read. The agent has a limited set of built-in tools: glob, grep, and read. It can discover relationships with these tools, but it burns tokens, relies on error-prone judgement, and injects bias by reading off-task content. 

The default tools operate over surface text, recovering only content channels — lexical and topical overlap, a shared rare term. Relatedness carried by graph topology, by commit and authorship provenance, by temporal proximity is inexpensive to recover but unreachable: no graph exists to traverse, no history to read. These channels are recoverable after the corpus is reified as a graph.

Hoplite augments the default navigation tools through a map over the markdown corpus. Instead of relying on the agent to read, comprehend, and infer relationships on-the-fly, Hoplite applies structure to the markdown and reifies the map as a durable graph with declared and latent relationships. The agent navigates the map and reads selectively, spending its context on the subset that matters.

## The compounding cost of the grep-read-judge loop

For the agent, knowledge that sharpens the context is useful. Content that contains useful knowledge is relevant. To acquire useful knowledge, the agent must first locate and consume relevant content.

The agent's default method of exploration, `grep`, is a primitive search tool that returns unranked and unordered results. The agent must sift through hits, loading each into the context and judging usefulness for itself. The exploration loop taxes scarce resources: time, tokens, turns, context budget, and bias-inducing attention. The quantitative and qualitative costs compound. Every wasted read is debt serviced for the life of the context.

Scanned noise biases the agent; so does signal it never reaches. `grep` matches only what the agent can name. Explore agents, guarding their context budget, scan excerpts and risk missing critical information. Hard won memory sits unused. The knowledge-starved agent exercises poor judgment: it reopens settled decisions, contradicts conventions, overwrites working code, and reproduces prior art. Failures compound.

The relationships discovered by the agent are the reward for every leaf it read and every dead end it ruled out. They live in the context window and nowhere else. They die with the session. The next agent re-derives them from scratch, or not. Cost compounds. Failure compounds. Knowledge that compounds is lost.

## Maximizing signal-to-noise to reduce cost

Hoplite builds a durable knowledge graph over the corpus — documents become nodes, relationships become edges, and the author's descriptions define the ontology's schema. The agent queries the map instead of scanning the bytes: it ranks what matches, walks relationships the filesystem can't show, and reads a document's summary before opening it. Locating and consuming — the costly acts — become a query and a choice.

Search returns ranked hits, each carrying its authored summary. The agent reads the lede, not the leaf, judging relevance from the summary before spending a token on the body. The map hands back a projection, never a document; the agent crosses to full content only for the hits that survive. The exploration loop collapses to a query and a few deliberate reads. The agent opens only what pays.

The map answers more than the agent asks. Search is closed-loop, returning what matches the query; discovery is open-loop. From any document the agent walks to its neighborhood — the links the author declared, the documents that point back, the kin no one wrote down but the engine inferred from shared terms, citations, tags, and time, location, and meaning. Ghosts keep the unwritten enumerable. Hard-won memory sits one hop away. The agent reaches what it never thought to name.

The relationships are derived once and persisted. They outlive the session that found them. The next agent inherits the map instead of re-deriving it: it walks to the rationale behind a decision before repeating it, and reads the prior art before rewriting it. The reward for every leaf read and every dead end ruled out is kept, not discarded. Every session adds to the graph; none starts from zero. Knowledge compounds.

The map is built in three movements: the author declares and describes explicit structure, the engine discovers latent structure, and the agent reads by navigating both.

### Declare and describe — applying explicit structure

The author asserts what the bytes can't yield: a relationship that lives only in a link, a title that isn't the filename, a summary the document never states. This is explicit structure — supplied, not inferred — and the graph treats it as fact.

A wikilink declares a relationship grep can't see: a directed edge from one document to another. A markdown link declares one too, reaching content outside the corpus — the graph's edges don't stop at its own files. Declared once, an edge reads both ways; the backlink, who points here, is free structure. Whether the tie is symmetric is the stereotype's call — `supersedes` runs one way, a `related` or `not-related` tie reads both. A ghost link declares an open loop: not-yet-written content made explicit rather than lost.

Description annotates the structure. A title and summary are asserted, not extracted — a filename is not a title, and a document carries no summary of itself. The summary is the lede the agent reads to decide whether to open the document or follow the edge. Properties — tags, status — classify a document and crosscut the folder it is filed in. A stereotype labels an edge with the kind of relationship it carries: cites, supports, supersedes, contradicts. Describe an edge inline beside the claim it makes, or in frontmatter as a document-level fact — same structure either way. The vocabulary is open: the author coins a label and it earns canonical status by use, the way tags do.

### Discover — inferring latent, emergent structure

Beyond what the author declared, the corpus holds relationships no one wrote down — implicit kinship that emerges from shared features. A declared edge is asserted and treated as fact; a latent signal is implied, present only as a pattern the engine recovers by inference.

Every inferred relationship is graded by the improbability of the coincidence — a rare shared feature, or a narrow shared window. Two documents sharing a common word carry no signal; two sharing a rare term carry a strong one. That grading is why discovered relationships can be ranked.

The signals resolve into three channels, each an independent feature space. Content and metadata measures what the documents say: topical similarity surfaces a kinship the author missed, and at its extreme gathers near-duplicates into one neighborhood instead of N strangers; a shared tag relates documents by kind even when their topics diverge; documents created close in time share the intent of whatever was underway, tracing an arc — genesis, build, refactor — that no one declared and that falls out of time. Structure measures topology, not content: two documents pointed to by the same third, pointing to the same third, citing the same external source, or naming the same rare entity couple through the shared connector — a rare connector strongly, a hub weakly. History measures provenance from the commit graph: documents changed in the same commit couple, often more strongly than their content suggests, as do documents edited in the same session or by the same author.

Latent signal buys recall at the cost of precision — it finds the connection the author missed, and sometimes one that isn't there. The threshold is the knob. Provenance ranks above score: every discovered tie is graded, but a declared edge carries full confidence and outranks any discovered one for the same pair. The author's word beats the engine's guess.

### Read — navigating mapped relationships

Affordances emerge from the mapped structure: survey the vocabulary, filter by meaning, walk relationships, project and read the results.

1. Survey — retrieve the schema vocabulary, properties and stereotypes, before composing a predicate over the corpus.
2. Filter — narrow the corpus to the subset a Boolean predicate admits (`note & mcp & !draft`): semantic search matches by meaning, not literal string or path; properties crosscut folders, so filtering by one gathers a concept wherever it lives.
3. Walk — traverse declared and discovered edges from a node to gather a neighborhood the tree can't show: a relationship declared once reads both ways (inbound and outbound edges); ghosts keep open loops enumerable.
4. Project — organize the resultset: sort it by score or distance, shape what each hit returns (the lede and tags, never the body), and cap the hops and result set size. Hoplite hands back a projection, not a document — so the agent judges relevance from the summary authored in [Describe](#declare-and-describe--applying-explicit-structure) before spending a token to open the file.
5. Read — the built-in Read tool. Hoplite ends at the projection; the agent crosses to full content only for the hits that survive.
