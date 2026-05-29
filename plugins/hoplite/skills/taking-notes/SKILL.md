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
document:
  tags: [<tag>, ...]
  created: YYYY-MM-DD
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

Every key beyond `title` and `summary` creates one of two things. A **node property** is a fact stored on the document's own graph node — a key with one or more values (`tags`, `created`, `status`). An **edge stereotype** is a labeled link from this document to another — a typed `mentions` edge carrying a name like `blocked_by` or `supports`.

`document` and `edge` are namespaces — they declare which of the two a key creates: `document.` for node properties, `edge.` for edge stereotypes. `title` and `summary` are the exception — they are first-class, FTS-indexed fields, not properties, so they stay **bare**.

Two mandatory fields:

- `title` (string, bare) — short, human-readable name.
- `summary` (string, bare) — one-line lede. `where` and `relatives` return it so callers can scan candidates without opening the file.

Optional fields:

- `document.created` (ISO date string, `YYYY-MM-DD`) — creation date. Stays stable across edits when present.
- `document.tags` (list of strings) — tag slugs the document carries. Use kebab-case lowercase (`graph-db`, not `Graph DB` or `graph_db`); the indexer casefolds for lookup. A document may carry no tags.
- `document.aliases` (list of strings) — alternate paths that resolve to this document; add on rename so wikilinks pointing at the old name still resolve.

`document.tags` and `document.aliases` are lists and follow the omit-when-empty rule: include the key only when it carries at least one element, otherwise leave it out.

Beyond the mandatory fields, any `document.<key>` becomes a node property and any `edge.<stereotype>: [paths]` becomes a stereotyped `mentions` edge — Hoplite accepts and stores them. Examples: `document.status: draft`, `document.priority: high`, `document.due: 2026-06-01`, `edge.blocked_by: [docs/notes/foo.md]`. External tools like Obsidian or Dataview read them too. Only `title` and `summary` are bare; everything else is prefixed.

### Namespace spelling and list spelling

A key carries spelling freedom on two independent axes — the namespace on the left, the list value on the right.

The **namespace** (`document`, `edge`) can be written two ways, and Hoplite normalizes both to the same key before indexing:

- **Dotted** — `document.tags: [...]`. The namespace is part of the key.
- **Nested** — a `document:` mapping with its keys indented underneath. Reads cleaner when a document carries several properties.

YAML treats these as different structures — `document.tags` is one key with a dot in its name; the nested form is a mapping under `document`. Hoplite's parser flattens the mapping to the dotted key, so the two are equivalent by Hoplite's rule, not YAML's. Neither is preferred. A file can mix them — a nested `document:` block alongside dotted `edge.<stereotype>` lines. `title` and `summary` stay bare in both forms.

A **list value** accepts any valid YAML sequence — flow or block are identical here, because YAML itself parses them to the same list:

```yaml
document.tags: [note, design]
```

```yaml
document.tags:
  - note
  - design
```

`document.tags`, `document.aliases`, and every `edge.<stereotype>` must be sequences. Any other `document.<key>` may be a bare scalar — `document.status: draft` stores as a single-value property, the same as `document.status: [draft]`.

### Tags classify; properties carry state

A tag answers "what is this document?" — its type, classification, the shape of artifact it represents. Tags are immutable once applied. Removing one erases the document's identity as that kind of artifact and breaks queries that rely on the classification.

A property answers "what state is this document in?" Fields that change as the lifecycle progresses (`document.status` moving from `open` to `closed`, `document.priority` re-triaged). State changes update the value, not the tag set.

State-as-tag is the anti-pattern — a `resolved`, `closed`, or `draft` tag conflates identity and state, because rewriting `document.tags` to track lifecycle churns the identity axis. Use a `document.status` property instead. The reverse also holds: do not invent a `document.type: <kind>` property to duplicate signal the type tag already carries.

Canonical example — dotted form:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
document.tags: [graph-db, note]
document.created: 2026-05-25
document.status: draft
---
```

The same document in nested form (the corpus convention), with an `edge.<stereotype>` line shown dotted alongside the nested `document:` block:

```yaml
---
title: Property graphs
summary: Notes on the property-graph data model and SQLite-vs-native tradeoffs.
document:
  tags: [graph-db, note]
  created: 2026-05-25
  status: draft
edge.supports: [docs/notes/sqlite-hybrid.md]
---
```

## Hoplite catalog

Hoplite is a knowledge graph over the markdown corpus at `docs/`. Each `.md` file is a document; YAML frontmatter at the top of each file feeds the index. Hoplite builds the graph in memory at MCP server startup.

Hoplite is the index; your built-in `Read`, `Write`, `Edit`, and `Bash rm` tools are the content surface. `Grep` and `Glob` are the literal surface — substrings in lines and filename patterns. Hoplite is the semantic surface: documents ranked by topical relevance (BM25 FTS over body and summary), filtered by predicate expressions, and reachable through authored `[[wikilink]]` paths (`mentions` edges) or inferred topical adjacency (`related` edges from MinHash similarity).

### Tools

- `where(predicate, k=5)` — rank documents by topical relevance, tag expression, or both. `text` runs BM25 over an FTS index of body and summary, so a query for `caching strategy` surfaces documents *about* caching rather than only lines containing the literal token. `tagged` filters by boolean tag expression: `note`, `note & mcp`, `(note | journal) & !draft`. At least one of `text`/`tagged` required. Returns up to `k` `Hit` records (path, summary, tags, score) ranked by score.
- `relatives(from_, predicate=None, depth=1)` — breadth-first walk from a starting document through authored `mentions` edges and inferred `related` edges. Surfaces neighborhoods the corpus author may or may not have explicitly linked: a `related` edge can connect two topically-adjacent documents with no wikilink between them. Returns `TraversalHit` records (path, summary, tags, distance, via_edges) for nodes at distance 1 through `depth`. Predicate fields (all optional): `edge_types` (`mentions`, `cites`, `related`), `top_k_related` (cap on the number of `related` neighbors followed per node, ranked by confidence — set to narrow the walk to each node's strongest similarities; omit to widen the walk and judge adjacency from the per-edge `confidence` in `via_edges`. `mentions` and `cites` are always followed.), `direction` (`out`/`in`/`both`), `tagged` (tag expression filter on reached documents).
- `refresh()` — rebuild the in-memory graph from the current state of the corpus. Call after writes so subsequent queries see the changes. Returns a `WriteResult` (`path` = corpus root, `warnings`).
- `export(path=None)` — debug. Snapshots the in-memory graph to a SQLite file (default `.hoplite/<ISO-timestamp>.index.sqlite` — each dump is uniquely named so prior snapshots survive). Then you can `Bash sqlite3 .hoplite/<file>` for arbitrary SQL exploration. Returns a `WriteResult` (`path` = snapshot file, `counts` with `documents`/`ghosts`/`edges`, `warnings`).

### Edges

Two edge kinds materialize. Edges connect documents to documents only — tag membership is a property, not an edge.

- `mentions` — document → document. One per `(source, target)` pair from `[[wikilink]]` occurrences in body text. Multiple wikilinks from one document to the same target collapse to a single edge. A `[[docs/<path>.md]]` target that lacks a backing file or a `[[ghost/<slug>]]` target creates a ghost document.
- `cites` — document → URL. One per `(source, url)` pair from inline `[text](https://...)` markdown links in body text. The dst node is keyed by the verbatim URL (no canonicalization); call `relatives(predicate={"edge_types": ["cites"]})` to list every external reference from a document.
- `related` — document ↔ document, symmetric. Emitted by MinHash similarity above threshold. Carries a `confidence` property holding the Jaccard score.

### Vocabulary

- Document — a node in the graph. Identified by its path: `docs/<sub>/<name>.md` for real markdown documents on disk, `ghost/<slug>` for intentional open loops, `https://...` (or `http://`) for URL-keyed nodes auto-indexed from inline markdown links. The same path appears in `Hit.path` and `TraversalHit.path` — for `docs/...` paths the agent can `Read` directly; for URL paths the agent has the URL itself to `WebFetch` or pass on.
- Tag — a free-form annotation authored in a document's frontmatter `document.tags` list. Tags are properties on documents, not separate nodes. Matched case-insensitively. Query with `tagged: <expression>`.
- Property — a key-value pair from a document's frontmatter. Each `document.<key>` becomes one or more node-property rows on the owning document. `title` and `summary` are bare, first-class FTS fields rather than properties; `edge.<stereotype>` keys author edges, not properties.
- Ghost document — a wikilink target without a backing file (`resolved = false`). Authored as `[[ghost/<slug>]]` for intentional open loops. First-class node in `relatives` results, so the corpus's unwritten cross-references stay visible. Walker injects a synthetic `ghost` tag so `where({"tagged": "ghost"})` enumerates them; URL nodes get a synthetic `url` tag the same way.
- Hit — a search result from `where`. Fields: `path`, `summary`, `tags`, `score`.
- TraversalHit — a result from `relatives`. Fields: `path`, `summary`, `tags`, `distance`, `via_edges`.
- WriteResult — returned by `refresh` and `export`. Fields: `path`, `counts` (optional), `warnings` (optional). The reindex's `warnings` list surfaces malformed wikilink targets (anything not starting with `docs/` or `ghost/`) so you can fix them.
- Wikilink — an in-body cross-reference between documents; materializes a `mentions` edge. Two valid shapes: `[[docs/<path>.md]]` for real refs and `[[ghost/<slug>]]` for intentional open loops.

## Titles

- Compresses to a short, distinctive handle — grep returns it, the reader recognizes it.
- States the artifact's claim, not its topic.
- Declarative, present-tense, specific.

Shape varies — claim, decision, question, reference. Defer to the user's request.

## Summaries

- Extends the title in its voice — adds what compression dropped.
- Front-loads — informative phrase first.
- Stands alone for the skim; bridges to the body for the read.

One to three sentences.

## Bodies

- Body proves the summary — summary the lede, body the evidence.
- Separates observation from interpretation — facts before meaning; two sentences or two sections mark the boundary.
- Every claim wears an epistemic badge — observation, inference, or guess. Unlabeled guesses pass as fact.
- Sentence-style headings — first word and proper nouns only; no title case.
- Numbered lists for procedures, bullets for options, prose for reasoning.
- Markdown links — `[text](path)` with text that names the target.
- Wikilinks — `[[docs/notes/coffee.md]]` for cross-artifact references. The target is the *full* repo-relative path including the `docs/` root and the `.md` extension. Query results return that same full path, so an agent can read the file without hunting it down. `[[docs/journal/2026-05-25-1430-roast.md]]` reaches a journal entry; an alias declared in a document's frontmatter resolves too.
- Open loops — an intentional reference to a not-yet-written document. Authored as `[[ghost/<slug>]]` — the `ghost/` prefix declares the intent explicitly, distinct from a malformed link. Ghost documents store under that path and surface in `relatives` results as the backlog of mentioned-but-unwritten work. When the file lands on disk, rewrite the link to its real `docs/...` path.
- External references — inline markdown `[text](https://...)` for casual citations. The walker indexes every such link as a URL-keyed graph node, connected by a `cites` edge — the link renders clickable in any markdown viewer and gets backlink-discoverable for free. For durable references that earn metadata (tags, summary, "why this matters") or are cited from multiple docs, write a proxy note at `docs/proxies/<slug>.md` carrying the URL plus context; wikilink the proxy from elsewhere.
- Sample wikilinks always wear backticks — illustrative `[[X]]`, `[[docs/notes/example.md]]`, or any wikilink-shaped string demonstrating syntax sits inside backticks or a fenced block. Bare `[[X]]` in prose materializes a ghost; the resolver treats backticked spans as code and skips them. Same rule applies to sample markdown URLs.
- Skip bold and tables — they add noise to the markdown, making it hard to read; except in worked examples that demonstrate what to remove.

## Composition

- Say what is, not what it isn't — except in contrastive pairs that sharpen the positive claim.
- Active voice over passive — agency stays with the actor; "the user signs in," not "sign-in is performed by the user."
- Present tense for current state — "the function returns," not "the function will return." Past tense fits journal observations.
- Second person for instructions — address the reader as "you."
- Concrete over abstract — "the cache" beats "the caching mechanism" unless the distinction is the point.
- One idea per sentence — split complex sentences.
- Strong verbs — over nominalizations ("decide" beats "make a decision") and verb-plus-adverb ("sprint" beats "run quickly").
- Every word earns its place — cut hedges, filler, transitions that announce.
- Substance over superlatives — the reader judges; cut hollow words like "seamless," "powerful," "easy."
- Assertions over commentary — let each statement stand; skip framing like "let's dive into."
- English over Latin — "for example" beats "e.g."; "that is" beats "i.e."; "and so on" beats "etc."
- Anticipate the reader's question — write what they need next, not what's next in your head.
- Front-load important words — most informative first, in sentence and bullet.

## Punctuation

- Em-dash (`—`) for parenthetical breaks, definitions, and appositives; not double hyphens.
- Oxford comma — `nodes, edges, and properties` for lists of three or more.
- Backticks for code, paths, identifiers, and CLI commands; fenced blocks with language tags for multi-line samples.

## Validation

- Lede check — first paragraph alone names what the artifact is for.
- Negation grep — `not`, `don't`, `doesn't`, `won't`, `can't`, `never`, `avoid` → positive rewrite, except contrastive pairs.
- Hedge and filler grep — `might`, `perhaps`, `simply`, `just`, `actually`, `really`, `quite`, `very` → cut.
- Tense drift grep — `will`, `would` → present tense.
- Marketing grep — `seamless`, `powerful`, `easy`, `intuitive` → substance.
- Latin grep — `e.g.`, `i.e.`, `etc.` → English equivalents.
- Bold and table grep — `**`, `|---|` → zero hits outside worked examples.

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
