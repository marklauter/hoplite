---
name: todo
description: Use when triaging notes tagged `todo` — assigning priority and effort, marking blockers, closing items the corpus has caught up with, or sweeping for action items the author hasn't yet labeled. Reach for it when the user asks to triage, prioritize, work the backlog, or review what's outstanding.
---

# Todo

A todo is a note tagged `todo` — an action item the corpus is tracking. The tag is immutable; state lives in three frontmatter properties so a todo's lifecycle stays queryable without rewriting its history.

## When to triage

Included:

- A note lands with the `todo` tag and no triage fields — assign priority, effort, dependencies, status.
- A note acquires action-item shape after the fact — add `todo` to its tags and triage.
- A todo's work landed — close it. The corpus catches up with the world.
- The user asks to sweep — find notes that read as action items but lack the `todo` tag, then triage them.

Excluded:

- Authoring the note itself. `taking-notes` handles composition; this skill operates on the result.
- Tracking deadlines, calendars, or assignment. The corpus records work shape, not who or when.

## What a todo is

The `todo` tag identifies a document as an action item — UML-stereotype-style label, immutable once applied. Removing the tag erases the document's identity as a todo. State lives in three properties; the tag answers "is this a todo?", the properties answer "how urgent, how costly, what's blocking, where in the lifecycle."

## Todo anatomy

Filename: the source note's path is unchanged. Todos live wherever the underlying note lives — `docs/notes/<slug>.md` for most.

Three properties on the document:

- `document.priority` — `high` | `medium` | `low`. The triager's read of urgency.
- `document.effort` — `high` | `medium` | `low`. Implementation cost as best understood at triage time. Verification often revises it; that is expected.
- `document.status` — lifecycle:
  - `open` — work to do.
  - `closed` — done. The body carries a `## Resolution` section naming where the change landed.
  - `deferred` — parked. Re-triage when conditions change (a blocker resolves, the corpus reaches the scale that justifies the work).
  - `declined` — decided not to do. The body explains why so the decision survives.

Dependencies are edge stereotypes:

- `edge.blocked_by: [<path>, ...]` — todos that must close before this one is workable. Mirrors the `edge.<stereotype>` namespace shared with `edge.contradicts` and `edge.not-related`.

Tags: `todo` plus the underlying note's domain tags. Status is a property, not a tag — adding `closed` or `resolved` as tags duplicates `document.status` and rots.

## Epics

A todo tagged `epic` decomposes into child todos. The epic's body wikilinks each child; `declared` edges materialize the hierarchy. `where({"tagged": "todo & epic"})` enumerates epics; `relatives({from_: <epic>, edge_types: ["declared"], tagged: "todo"})` walks the children.

The epic's own `document.status` reflects the rollup of its children — `open` while any child stays `open` or `deferred`, `closed` once every child is `closed` or `declined`. The triager sets the rollup explicitly until a computed-property pass automates it.

## Triage as a pattern

Priority and effort are both the triager's read at triage time, and both are revisable. Effort calls earn confidence when the triager reads the code the note points at, not just the note itself.

Verification — reading the named file, function, or commit — often surfaces three shapes:

- Closure. The fix already landed; set `document.status: closed` and add a `## Resolution` section pointing at where.
- Fork. The note hides two unrelated changes; split into two notes and triage each.
- Revised effort. What the note self-described as "localized" turns out to need migration, tests, or a schema change.

Sweep mode finds action-shaped notes that lack the `todo` tag. Tag them and triage them.

## Artifact structure

An artifact covers exactly one topic. It is composed of YAML frontmatter and a markdown body.

See [Frontmatter](#frontmatter).

Template:

```markdown
---
title: <title>
summary: <one-line summary>
tags: [<tag>, ...]
created: YYYY-MM-DD
document: # optional — node properties, named value axes (status, severity, ...)
  status: <lifecycle state, e.g. open>
---

# <one-line title>

<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```

## Frontmatter

Every document in the Hoplite corpus, docs/, opens with a YAML frontmatter block. Hoplite indexes documents through this block; a document with missing or malformed frontmatter generates a warning at reindex (in `WriteResult.warnings`) and stays out of the graph until you fix it.

Five keys are bare — written flat at the top level, no namespace prefix: `title`, `summary`, `tags`, `created`, and `aliases`. `title` and `summary` are first-class FTS-indexed fields; `tags`, `created`, and `aliases` are recognized fields the indexer maps to their roles (classification, creation date, alternate paths). Every other key is namespaced. A **node property** — a fact stored on the document's own graph node — is written `document.<key>`. An **edge stereotype** — a labeled link from this document to another, a typed `declared` edge — is written `edge.<stereotype>`.

Two mandatory fields:

- `title` (string, bare) — short, human-readable name.
- `summary` (string, bare) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.

Optional bare fields:

- `created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits when present.
- `tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup. A document may carry no tags.
- `aliases` (list of strings) — alternate paths that resolve to this document; add on rename so wikilinks pointing at the old name still resolve.

`tags` and `aliases` are lists and follow the omit-when-empty rule: include the key only when it carries at least one element, otherwise leave it out.

Beyond the bare fields, any `document.<key>` becomes a node property and any `edge.<stereotype>: [paths]` becomes a stereotyped `declared` edge — Hoplite accepts and stores them. Examples: `document.status: draft`, `document.priority: high`, `document.due: 2026-06-01`, `edge.blocked_by: [docs/notes/foo.md]`. External tools like Obsidian or Dataview read them too.

### Namespace spelling and list spelling

A namespaced key carries spelling freedom on two independent axes — the namespace on the left, the list value on the right. The bare fields (`title`, `summary`, `tags`, `created`, `aliases`) take neither; they are always flat.

The **namespace** (`document`, `edge`) can be written two ways, and Hoplite normalizes both to the same key before indexing:

- **Dotted** — `document.status: draft`. The namespace is part of the key.
- **Nested** — a `document:` mapping with its keys indented underneath. Reads cleaner when a document carries several properties.

YAML treats these as different structures — `document.status` is one key with a dot in its name; the nested form is a mapping under `document`. Hoplite's parser flattens the mapping to the dotted key, so the two are equivalent by Hoplite's rule, not YAML's. Neither is preferred. A file can mix them — a nested `document:` block alongside dotted `edge.<stereotype>` lines.

A **list value** accepts any valid YAML sequence — flow or block are identical here, because YAML itself parses them to the same list:

```yaml
tags: [note, design]
```

```yaml
tags:
  - note
  - design
```

`tags`, `aliases`, and every `edge.<stereotype>` must be sequences. Any `document.<key>` may be a bare scalar — `document.status: draft` stores as a single-value property, the same as `document.status: [draft]`.

### Tags are set membership; properties are named axes

A tag is unnamed set membership — the document carries `note` or it doesn't. You filter with boolean tag expressions (`note & !draft`). Tags answer "what is this document?": its type, classification, the shape of artifact it represents. They are immutable once applied; removing one erases the document's identity as that kind of artifact and breaks queries that rely on the classification.

A property is a named axis holding a value — `severity` is the axis, `high` is the value. The value can be lifecycle state (`document.status` moving from `open` to `closed`), an ordered grade (`document.severity: high|med|low`), or a descriptive category (`document.issue-type: doc|code`). State is one kind of value a property carries, not what defines it; what defines a property is the named axis.

The deciding question between the two: do you need the axis name? If you will ask "what is the severity?" or want exactly one value on a known dimension, use a property. If you only need "is it tagged `doc`?", use a tag.

Two anti-patterns fall out. State-as-tag — a `resolved`, `closed`, or `draft` tag forces lifecycle churn through the identity axis; use a `document.status` property instead. Axis-duplication — a `document.type: <kind>` property duplicates signal a type tag already carries; let the tag answer it.

Canonical example:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, note]
created: 2026-05-25
document.status: draft
---
```

The same document with a nested `document:` block and an `edge.<stereotype>` line — bare fields stay flat above it:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
tags: [graph-db, note]
created: 2026-05-25
document:
  status: draft
  priority: high
edge.supports: [docs/notes/sqlite-hybrid.md]
---
```

## Hoplite catalog

Hoplite is a knowledge graph over the markdown corpus at `docs/`. Each `.md` file is a document; YAML frontmatter at the top of each file feeds the index. Hoplite builds the graph in memory at MCP server startup.

Hoplite is the index; your built-in `Read`, `Write`, `Edit`, and `Bash rm` tools are the content surface. `Grep` and `Glob` are the literal surface — substrings in lines and filename patterns. Hoplite is the semantic surface: documents ranked by topical relevance (BM25 FTS over body and summary), filtered by predicate expressions, and reachable through authored `[[wikilink]]` paths (`declared` edges) or inferred adjacency (`discovered` edges from similarity and other shared-feature signals).

### Tools

- `where(predicate, k=5)` — rank documents by topical relevance, tag expression, or both. `text` runs BM25 over an FTS index of body and summary, so a query for `caching strategy` surfaces documents *about* caching rather than only lines containing the literal token. `tagged` filters by boolean tag expression: `note`, `note & mcp`, `(note | journal) & !draft`. At least one of `text`/`tagged` required. Returns up to `k` `Hit` records (path, summary, tags, score) ranked by score.
- `relatives(from_, predicate=None, depth=1)` — breadth-first walk from a starting document through authored `declared` edges and inferred `discovered` edges. Surfaces neighborhoods the corpus author may or may not have explicitly linked: a `discovered` edge can connect two topically-adjacent documents with no wikilink between them. Returns `TraversalHit` records (path, summary, tags, distance, via_edges) for nodes at distance 1 through `depth`. Predicate fields (all optional): `edge_types` (`declared`, `discovered`), `top_k_discovered` (cap on the number of `discovered` neighbors followed per node, ranked by confidence — set to narrow the walk to each node's strongest signals; omit to widen the walk and judge adjacency from the per-edge `confidence` in `via_edges`. `declared` edges are always followed.), `direction` (`out`/`in`/`both`), `tagged` (tag expression filter on reached documents).
- `refresh()` — rebuild the in-memory graph from the current state of the corpus. Call after writes so subsequent queries see the changes. Returns a `WriteResult` (`path` = corpus root, `warnings`).
- `export(path=None)` — debug. Snapshots the in-memory graph to a SQLite file (default `.hoplite/<ISO-timestamp>.index.sqlite` — each dump is uniquely named so prior snapshots survive). Then you can `Bash sqlite3 .hoplite/<file>` for arbitrary SQL exploration. Returns a `WriteResult` (`path` = snapshot file, `counts` with `documents`/`ghosts`/`edges`, `warnings`).

### Edges

Two edge kinds materialize, by provenance — who asserted the edge, not what it means. Edges connect documents to documents only; tag membership is a property, not an edge.

- `declared` — the author asserted it by writing a `[[wikilink]]` in body text. One per `(source, target)` pair, however many wikilinks point the same way; `confidence` is `1.0`. A `[[docs/<path>.md]]` target lacking a backing file, or a `[[ghost/<slug>]]` target, creates a ghost document. An inline `[text](https://...)` markdown link declares an edge whose `dst` is a URL node.
- `discovered` — the engine inferred it from a shared feature: content similarity (MinHash), co-citation, temporal proximity, and the rest. Symmetric where the signal is. `confidence` holds the graded strength.

What a declared edge *means* — a citation, a refutation, an endorsement — is an open-vocabulary stereotype stored as an edge property, never a kind; a bare edge with no stereotype is just a link. To enumerate a document's external references, walk its `declared` edges and keep the destinations carrying the synthetic `url` tag.

### Vocabulary

- Document — a node in the graph. Identified by its path: `docs/<sub>/<name>.md` for real markdown documents on disk, `ghost/<slug>` for intentional open loops, `https://...` (or `http://`) for URL-keyed nodes auto-indexed from inline markdown links. The same path appears in `Hit.path` and `TraversalHit.path` — for `docs/...` paths the agent can `Read` directly; for URL paths the agent has the URL itself to `WebFetch` or pass on.
- Tag — a free-form annotation authored in a document's bare top-level `tags` list. Tags are properties on documents, not separate nodes. Matched case-insensitively. Query with `tagged: <expression>`.
- Property — a key-value pair from a document's frontmatter. Each `document.<key>` becomes one or more node-property rows on the owning document. `title` and `summary` are bare, first-class FTS fields, and `tags`, `created`, and `aliases` are bare recognized fields; `edge.<stereotype>` keys author edges, not properties.
- Ghost document — a wikilink target without a backing file (`resolved = false`). Authored as `[[ghost/<slug>]]` for intentional open loops. First-class node in `relatives` results, so the corpus's unwritten cross-references stay visible. Walker injects a synthetic `ghost` tag so `where({"tagged": "ghost"})` enumerates them; URL nodes get a synthetic `url` tag the same way.
- Hit — a search result from `where`. Fields: `path`, `summary`, `tags`, `score`.
- TraversalHit — a result from `relatives`. Fields: `path`, `summary`, `tags`, `distance`, `via_edges`.
- WriteResult — returned by `refresh` and `export`. Fields: `path`, `counts` (optional), `warnings` (optional). The reindex's `warnings` list surfaces malformed wikilink targets (anything not starting with `docs/` or `ghost/`) so you can fix them.
- Wikilink — an in-body cross-reference between documents; materializes a `declared` edge. Two valid shapes: `[[docs/<path>.md]]` for real refs and `[[ghost/<slug>]]` for intentional open loops.

## Comprehension

Comprehension is the spine: understand the subject before you write it. Clear prose is the residue of clear thought — every section below is what conveying that understanding to a reader looks like at one scope.

- Understand first — you cannot compress what you have not grasped. Vague prose is a vague grasp padded out to hide the gap; the fix is upstream, in the thinking, not in the editing.
- Concision follows — once the subject is understood you know which words carry weight, so the rest falls away on its own. Aim at understanding and let economy be its consequence, not a separate goal.
- Shortest complete version — cut whole sentences and sections, not only words. Length is earned by purpose, not spent to look thorough.
- Say it once — each point gets one statement and one home.
- The exact word over the easy one — understanding picks the precise term; cut the filler around it, keep the substance and needed detail.
- Every section earns its place — keep a passage only when the artifact needs it to do its job.

## Titles

The tightest compression of the claim.

- A short, distinctive handle — grep returns it, the reader recognizes it.
- States the artifact's claim, not its topic.
- Declarative, present-tense, specific.

Shape varies — claim, decision, question, reference. Defer to the user's request.

## Summaries

One decompression up from the title — extends it in the same voice, adding what the handle dropped.

- Front-loads — informative phrase first.
- Stands alone for the skim; bridges to the body for the read.

One to three sentences.

## Bodies

The full claim — the lede's assertion, now carrying its evidence and only that.

- Separates observation from interpretation — facts before meaning; two sentences or two sections mark the boundary.
- Every claim wears an epistemic badge — observation, inference, or guess. Unlabeled guesses pass as fact.
- Each section stands alone — a search hit returns one section, not the whole document. Its first sentence names the subject so a reader arriving cold can follow it. Buy that independence with orientation, not duplication: name the subject and resolve referents — both cheap — and link to the home of any fact you would otherwise restate, never copy it.
- Sentence-style headings — first word and proper nouns only; no title case.
- Numbered lists for procedures, bullets for options, prose for reasoning.
- Markdown links — `[text](path)` with text that names the target.
- Wikilinks — `[[docs/notes/coffee.md]]` for cross-artifact references. The target is the *full* repo-relative path including the `docs/` root and the `.md` extension. Query results return that same full path, so an agent can read the file without hunting it down. `[[docs/journal/2026-05-25-1430-roast.md]]` reaches a journal entry; an alias declared in a document's frontmatter resolves too.
- Open loops — an intentional reference to a not-yet-written document. Authored as `[[ghost/<slug>]]` — the `ghost/` prefix declares the intent explicitly, distinct from a malformed link. Ghost documents store under that path and surface in `relatives` results as the backlog of mentioned-but-unwritten work. When the file lands on disk, rewrite the link to its real `docs/...` path.
- External references — inline markdown `[text](https://...)` for casual citations. The walker indexes every such link as a URL-keyed graph node, connected by a `declared` edge to that URL node — the link renders clickable in any markdown viewer and gets backlink-discoverable for free. For durable references that earn metadata (tags, summary, "why this matters") or are cited from multiple docs, write a proxy note at `docs/proxies/<slug>.md` carrying the URL plus context; wikilink the proxy from elsewhere.
- Sample wikilinks always wear backticks — illustrative `[[X]]`, `[[docs/notes/example.md]]`, or any wikilink-shaped string demonstrating syntax sits inside backticks or a fenced block. Bare `[[X]]` in prose materializes a ghost; the resolver treats backticked spans as code and skips them. Same rule applies to sample markdown URLs.
- Skip bold and tables — they add noise that makes the raw markdown hard for a human to read, and a table shreds prose into cells that shingle and embed poorly, so Hoplite ranks the content worse. Both audiences lose. The exception is a worked example that demonstrates what to remove.

## Composition

Economy at the sentence and word.

- Say what is, not what it isn't — except in contrastive pairs that sharpen the positive claim.
- Active voice over passive — agency stays with the actor; "the user signs in," not "sign-in is performed by the user."
- Present tense for current state — "the function returns," not "the function will return." Past tense fits journal observations.
- Second person for instructions — address the reader as "you."
- Concrete over abstract — "the cache" beats "the caching mechanism" unless the distinction is the point.
- One idea per sentence — split complex sentences.
- Name the referent over a distant pronoun — `it`, `they`, and `this` lose their antecedent across a heading or a long gap, and a reader often arrives mid-document from a search hit. A pronoun within its paragraph is clear; across a section boundary, repeat the noun.
- Strong verbs — over nominalizations ("decide" beats "make a decision") and verb-plus-adverb ("sprint" beats "run quickly").
- Every word earns its place — cut hedges, filler, transitions that announce.
- Substance over superlatives — the reader judges; cut hollow words like "seamless," "powerful," "easy."
- Assertions over commentary — let each statement stand; skip framing like "let's dive into."
- Anticipate the reader's question — write what they need next, not what's next in your head.
- Front-load important words — most informative first, in sentence and bullet.

## Consistency

One name per idea, one home per fact — across the whole corpus, not just the document.

- One canonical term per concept — pick a single term and reuse it verbatim. Elegant variation ("asserted feature," "author assertion," and "meta-assertion" for one idea) reads as craft to a human but fragments retrieval: an agent matches on exact tokens and clusters embeddings by them, so synonyms scatter what should rank together. Vary the sentence, never the term.
- Single source of truth — each fact has one home document; everywhere else links to it instead of restating it. This is "say it once" widened to the corpus: a restated fact drifts out of sync and dilutes the ranking with near-duplicates, while a link stays correct and reachable.

## Punctuation

The fewest marks that carry the structure.

- Em-dash (`—`) for parenthetical breaks, definitions, and appositives; not double hyphens.
- Oxford comma — `nodes, edges, and properties` for lists of three or more.
- Backticks for code, paths, identifiers, and CLI commands; fenced blocks with language tags for multi-line samples.

## Voice

Same voice as the underlying note — declarative, present-tense, terse. Reasoning lives in the body; frontmatter records the triager's call. A `## Resolution` section closes a todo by naming where the change landed — file path, function, or commit, concrete enough that a reader can verify without re-walking the conversation.
