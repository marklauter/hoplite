---
title: Genesis — modeling a property graph in SQLite
summary: A verbatim Claude Code transcript from 2026-05-24, before Hoplite had a name. An engineer-to-engineer intro to property graphs — model, native storage, traversal — that lands on the edges-are-just-nodes argument and on rolling a two-table node/edge schema over SQLite with recursive-CTE traversal. The design seed the specs and glossary later grew from.
tags: [journal, hoplite]
created: 2026-05-24
---

# Genesis — modeling a property graph in SQLite

This is the origin conversation, kept verbatim. On 2026-05-24, before Hoplite existed as a project, this Opus 4.7 session worked through property graphs from first principles and arrived at the decisions Hoplite is built on:

- the property-graph model — nodes and edges both first-class, each a label plus a property map — which became the graph in [[docs/hoplite/hoplite-graph.md]];
- the edges-are-just-nodes argument (the presheaf on `E ⇒ V`, subdivision, the line-graph functor) behind the substrate model;
- a two-table `nodes`/`edges` schema over SQLite with covering indexes and recursive-CTE traversal — the seed of `schema.sql`, of [[docs/hoplite/glossary/walk.md]] as the recursive CTE, and of the edge-type filter as an edge predicate;
- Cypher ergonomics versus rolling your own over SQLite, with the verdict "roll the two-table schema yourself" — the lineage of the later decision not to ship a Cypher-like query language, captured in [[docs/hoplite/hoplite-read-model.md]].

It is preserved as mining stock — raw transcript, not corpus prose. It records what was believed that day; later specs supersede its details. It is never to be corrected; a correction is a new entry.

## Transcript

```text
 ▐▛███▜▌   Claude Code v2.1.150
▝▜█████▛▘  Opus 4.7 · Claude Max
  ▘▘ ▝▝    D:\claude\claude

❯ /clear
  ⎿  (no content)

❯ i need an intro to property graph concept. start with brief usecase. then
  typical storage structure. then how they're used in graph traversal. are they
   just another kind of adjacency list? i'm a software engineer with 30 years,
  so you can be brief.

● Property Graphs

  Use case

  You're modeling a domain where the relationships carry as much meaning as the
  entities, and queries pivot on traversal rather than joins. Fraud detection
  ("find rings of accounts that transact in cycles"), recommendation
  ("friends-of-friends who bought X"), knowledge graphs, network/IT topology,
  dependency analysis. Relational schemas handle this badly past 2–3 hops —
  recursive CTEs and self-joins blow up.

  The property graph model: nodes and edges are both first-class, both have a
  label (type) and a property map (arbitrary k/v). Edges are directed and have
  their own identity. Contrast with RDF triples, where an edge is just (subject,
   predicate, object) with no room for edge attributes without reification.

  (Alice:Person {age: 34}) -[:KNOWS {since: 2019, weight: 0.8}]-> (Bob:Person
  {age: 31})

  Storage

  Real implementations vary, but the canonical "native" layout (Neo4j-style) is
  fixed-size record files with pointer chasing:

  - Node store: fixed-width records. Each node holds a pointer to its first
  relationship and its first property.
  - Relationship store: fixed-width records. Each edge is in a doubly-linked
  list per endpoint — it stores (startNode, endNode, type, prevRelForStart,
  nextRelForStart, prevRelForEnd, nextRelForEnd, firstProperty). The same
  physical edge record participates in two linked lists, one per side.
  - Property store: separate, often a linked chain of property blocks; large
  values spill to a dynamic store.
  - Label/type indexes for "find me all Person nodes" entry points.

  Fixed-width records mean recordId → file offset is pure arithmetic — no B-tree
   lookup to resolve a node or edge by id. That's the trick.

  Other backends pick different tradeoffs: TigerGraph and KuzuDB use columnar
  CSR (compressed sparse row); JanusGraph/DGraph layer the model over
  Cassandra/Badger; many "graph DBs" are really document stores with edge
  indexes (Neptune, Cosmos). The model is the same; the physics differ.

  Traversal

  Given a node, the engine reads its firstRelationship pointer, then walks the
  linked list — each hop is a pointer dereference into the relationship store,
  then into the node store for the neighbor. O(1) per edge traversed,
  independent of total graph size. This is the property that breaks the
  relational analog: a SQL join's cost scales with the joined table; a graph
  hop's cost scales with the degree of the current node.

  So for MATCH (a)-[:KNOWS*1..4]-(b), the engine does a BFS/DFS by chasing
  pointers, filtering on edge type and property predicates as it goes.
  Cypher/Gremlin compile to plans that look more like nested-loop traversals
  than relational joins.

  Is it just an adjacency list?

  Conceptually yes; operationally no. A property graph is an adjacency-list
  model — each node knows its incident edges. The differences from "an adjacency
   list in a hashmap":

  1. Edges are first-class records with their own id, type, and properties. An
  adjacency list usually models edges as bare neighbor refs.
  2. Bidirectional indexing for free — that doubly-linked-per-endpoint trick
  means you traverse in or out from either side without maintaining two
  structures.
  3. Persistent, transactional, indexed — secondary indexes on properties, ACID,
   MVCC, query planner. An in-memory adjacency list has none of that.
  4. Schema-optional typing via labels/types, so the engine can prune traversals
   by edge type cheaply.

  Mental model: it's an adjacency list that's been promoted to a database —
  edges have identity and attributes, and the storage layout makes "follow edges
   from this node" the O(1) primitive instead of "look up rows where fk = x."

✻ Brewed for 29s

❯ when you say an edge is a first-class record do you mean they are really just
   nodes from the storage engine perspective?

● No — separate store, separate record shape. "First-class" means they have
  identity and attributes, not that they share a representation with nodes.

  In the Neo4j-style layout:

  - Node records are one fixed-width shape in neostore.nodestore.db: (inUse,
  firstRelId, firstPropId, labels, …). ~15 bytes.
  - Relationship records are a different fixed-width shape in
  neostore.relationshipstore.db: (inUse, startNodeId, endNodeId, type,
  prevRelForStart, nextRelForStart, prevRelForEnd, nextRelForEnd, firstPropId).
  ~34 bytes.

  Different files, different record sizes, different fields. An edge record
  carries four pointers (the doubly-linked-list participation on both endpoints)
   that a node record has no analog for; a node record has a labels field an
  edge has no analog for.

  What they share:

  1. Both point into the same property store. A node's properties and an edge's
  properties are the same kind of thing on disk — a chain of property blocks.
  From the property store's perspective, "who owns this chain" is opaque.
  2. Both have stable ids addressable by id → fileOffset arithmetic.
  3. Both can be returned, filtered, and bound to variables in Cypher (MATCH
  (n)-[r]->(m) RETURN r.since).

  So "first-class" is a query-model and API claim: edges are addressable,
  attributable entities you can pin variables to and read properties off — not
  anonymous tuples like RDF triples or bare neighbor refs in an adjacency list.
  At the storage layer they're a distinct record type optimized for the one job
  nodes don't do: being walked as a doubly-linked list from two sides at once.

  Aside: some graph engines do collapse the distinction. RDF stores treat
  everything as triples. Some property-graph-on-KV implementations (JanusGraph)
  encode edges as entries in the source node's adjacency list with no
  independent record — closer to "edges are just neighbor entries with a
  property bag." Neo4j's native store is the canonical "edges are their own
  thing" design; it's a design choice, not a definitional requirement of the
  property-graph model.

✻ Churned for 16s

❯ but edges really are just nodes. edges are just neighbors. adjoint proves
  this in my opinion.

● Fair — the formalism agrees with you, and I was conflating "the storage layer
  distinguishes them" with "they're ontologically different things." They're
  not.

  A directed multigraph is just a presheaf on the walking parallel pair E ⇒ V —
  two sets and two functions source, target: E → V. From inside that category, V
   and E are symmetric objects; the only thing breaking the symmetry is which
  arrows happen to go between them. Edges are nodes that happen to have two
  distinguished outbound incidences. That's the bipartite incidence encoding:
  any graph G is faithfully represented as a bipartite graph on V ⊔ E with
  incidence edges — and the functor G ↦ B(G) is fully faithful, with adjoints in
   both directions to the obvious forgetful functors. So yes: edges are just
  nodes with a constraint.

  Subdivision makes this concrete and constructive — Sub(G) replaces each edge e
   with a fresh vertex v_e and two edges. After subdivision every original edge
  is literally a node, the graph carries the same information, and traversal
  semantics are preserved up to path-length rescaling. The line graph functor L
  does the dual move: edges become vertices, adjacency becomes "shared
  endpoint." Both constructions only make sense because edges were already nodes
   wearing a different hat.

  So the honest framing of what I said before:

  - Mathematically: edges = nodes-with-arity-2-incidence. The property-graph
  model is a special case of a typed bipartite graph, or equivalently a
  hypergraph restricted to 2-edges. No ontological gap.
  - Implementation-level: native graph engines specialize the 2-incidence case
  because it lets them encode incidence as two pointers per edge record and walk
   it as a linked list in O(1). If you stored edges as generic nodes with two
  incidence-edges each, every hop becomes three pointer chases instead of one,
  and you've thrown away the constant factor that makes graph traversal beat
  relational joins.

  The storage asymmetry is a performance optimization over a structure that's
  symmetric in the math. RDF stores and hypergraph databases (e.g.,
  HypergraphDB, AtomSpace) actually take the symmetric view seriously — edges
  are nodes, can themselves be endpoints of other edges, and you get reification
   for free. The price is exactly the indirection Neo4j's record layout exists
  to avoid.

  So: you're right about the structure, I was describing the engineering. The
  "first-class record" language was sloppy — what I should have said is "the
  storage engine special-cases the 2-incidence node and calls it an edge."

✻ Cogitated for 39s

❯ but they are conceptually different.. i tend to over abstract. i'm ENTP. lol.
   i don't see a reason why I can't model the property graph in SQLite

● You absolutely can, and people do — it's a reasonable choice for graphs up to
  maybe low tens of millions of edges, or anytime you want a single-file
  embedded store with ACID and SQL escape hatches.

  Minimal schema

  CREATE TABLE nodes (
    id      INTEGER PRIMARY KEY,
    label   TEXT NOT NULL,
    props   TEXT  -- JSON
  );

  CREATE TABLE edges (
    id        INTEGER PRIMARY KEY,
    src       INTEGER NOT NULL REFERENCES nodes(id),
    dst       INTEGER NOT NULL REFERENCES nodes(id),
    type      TEXT NOT NULL,
    props     TEXT  -- JSON
  );

  CREATE INDEX edges_src ON edges(src, type);
  CREATE INDEX edges_dst ON edges(dst, type);
  CREATE INDEX nodes_label ON nodes(label);

  That's the whole model. The two covering indexes give you the "walk
  outgoing/incoming edges of a node filtered by type" primitive in O(log n + k)
  where k is degree — not the O(k) you get from native pointer chasing, but the
  log factor is small and cache-friendly.

  Traversal

  SQLite has recursive CTEs, which is exactly the graph traversal hammer:

  WITH RECURSIVE reach(id, depth) AS (
    SELECT :start, 0
    UNION
    SELECT e.dst, r.depth + 1
    FROM reach r JOIN edges e ON e.src = r.id
    WHERE r.depth < 4 AND e.type = 'KNOWS'
  )
  SELECT DISTINCT id FROM reach WHERE depth > 0;

  JSON1 extension (built into modern SQLite) lets you predicate on properties:
  WHERE json_extract(props, '$.weight') > 0.5.

  Where it's fine

  - Embedded apps, desktop tools, on-device graphs.
  - Knowledge graphs in the millions-of-edges range.
  - Anything where you want a single file you can cp and version.
  - Prototyping before you know whether you need Neo4j.

  Simon Willison's datasette ecosystem, several note-taking apps (Obsidian-style
   backlink graphs), and plenty of bioinformatics tools do exactly this.

  Where it falls over

  1. Deep traversals at scale. Recursive CTE with millions of intermediate rows
  materializes into a temp B-tree. Native engines stream pointer hops with no
  intermediate set. Past ~6–8 hops on a dense graph, you'll feel it.
  2. Variable-length path planning. SQLite's planner doesn't know "this is a
  graph query" — no cardinality estimates on path expansion, no bidirectional
  BFS, no pruning by index-only edge-type scans. You hand-write the strategy.
  3. Concurrent writers. SQLite serializes writes. Fine for most embedded uses,
  bad for a write-heavy service.
  4. Query ergonomics. Cypher's MATCH (a)-[:KNOWS*1..3]->(b) becomes 15 lines of
   CTE. Worth it for small projects; painful when patterns get complex.

  Middle ground

  If you want the Cypher-shaped API without giving up the SQLite substrate, look
   at KùzuDB — embedded, single-file, columnar, speaks Cypher, designed to be
  the SQLite of graph databases. That's probably the closest thing to "SQLite
  but a property graph" as a product.

  But for a 30-year engineer who tends to over-abstract: rolling the two-table
  schema yourself is the right move 80% of the time. You'll learn more, the data
   model stays inspectable with any SQL client, and you can migrate to a real
  graph engine if the traversal cost ever becomes the bottleneck — which, for
  most projects, it doesn't.

✻ Brewed for 25s
```
