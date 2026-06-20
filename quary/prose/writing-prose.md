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
