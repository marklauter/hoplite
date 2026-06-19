---
name: taking-notes
description: Use when the user asks to write something down, save something for later, record something, take a note, or capture an open question — or when a discovery worth preserving emerges in conversation. Notes go under docs/notes/.
---

# Taking notes

A note is a durable artifact stored in `docs/notes/`. Notes survive beyond short-term memory and context windows. Anything worth remembering belongs in a note: a hypothesis, a measurement, a decision, a question, a reference, and so on.

Recording a note has four steps: spot the trigger, search for an existing note on the topic, compose the content, and save the file.

## Spot the trigger — when to record a note

Record a note when:

1. The user asks. They request a note; you compose one.
2. A discovery surfaces. A new graph connection between concepts: resolving an open question in conversation context, uncovering a connection between previously-unconnected ideas, comprehending a mechanism for the first time, unpacking a complex idea into parts, packing related ideas into a unified concept, or crystallizing an unknown into a precise question. You propose a note; the user approves or denies before you compose. Recording a dead end prevents repeating it.
3. Auto-capture mode is on. The user has asked you to auto-capture discoveries without the approval gate; discovery signals are the same as #2.

## Search for an existing note — duplicate hygiene

Before recording, look for an existing note on the topic. Glob `docs/notes/*.md` to list; Grep H1 titles with `^# ` or content with topic keywords.

- Same topic exists. Edit the existing file in place. Replace it wholesale only on user request or approval.
- Adjacent topic exists. Compose a new note and cross-reference it.
- Existing note covers the content with nothing to add. Surface "there's already a note on this topic" instead of recording a duplicate.
- Question note gained its answer. Write under the new declarative slug and delete the old; the title pivots from interrogative to declarative.

Preserve content. User-requested change mutates freely; agent-initiated change is additive — overwrite only on request or approval.

## Compose the note — topics and exclusions

Notes are repo-scoped; cross-repo facts, user profile, and persistent preferences belong in memory.

Each note covers one topic. Two topics get two notes — stuffing both into one breaks dedup and search.

Exclude from notes:

- Discoverable content — anything the authoritative source (code, CLAUDE.md, git history, other notes, directory structure) already states. Reference by stable identifier; duplication drifts as the source changes.
- Conversational ephemera — recap of what was just said, transcript of what was tried. Capture the durable finding, not the path to it.

## Tag the note — type, domain, status

Every note carries a `tags` array in its frontmatter. Three categories of tags compose, applied in order:

1. **Type tag — required: `note`.** Every note authored by this skill includes `note` as a tag. Distinguishes from journal entries (`journal`), references, decisions, and other artifact types that may share the corpus.
2. **Domain tags — what the note is about.** Pick from the existing vocabulary when possible — query the corpus (`where({"tagged": "<slug>"})` or grep `docs/notes/*.md` frontmatter) to see what's in use. Examples in active use: `hoplite`, `mcp`, `python`, `claude-code`, `skills`, `bash`, `architecture`, `design`. Add a new domain tag only when no existing slug fits.
3. **Status or shape tags — optional.** Capture intent or maturity when it shapes how the note reads: `bug`, `todo`, `decision`, `observation`, `superseded`, `open-question`. Use sparingly; only when the reader benefits from the framing.

Aim for three to six tags total — enough that the note surfaces in tag queries, few enough that each tag earns its place. Slugs are kebab-case lowercase (`graph-db`, not `Graph DB`).

## Save the file

Notes are saved at `docs/notes/<slug>.md` where `<slug>` is a lowercase slug of the H1 title. Glob the target path first to learn whether the note exists. For a new note, use Write. For an existing note, use Edit to extend the body — adding content needs no approval. Removing content, or replacing the file wholesale, requires user approval. After saving, confirm with a minimal acknowledgment — for example, `note saved: <slug>.md`. No recital or recap.

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

## Rhetorical context

- Writer: contributor
- Voice: declarative, terse
- Ethos: expert
- Stance: neutral
- Audience: a future reader picking up where this session left off — the same agent after compaction, a different agent in a later session, or the user revisiting
- Subject: any repo-scoped topic worth a durable record — discoveries, decisions, observations, open questions, dead ends, design fragments
- Genre: note
- Tone: professional, even-keeled
- Register: declarative, present-tense, mutable and always current; the note evolves as understanding does and replaces prior content rather than versioning it
- Intent: externalize repo-scoped findings into structured, retrievable artifacts that survive context compaction
