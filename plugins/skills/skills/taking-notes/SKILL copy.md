<!-- design scratch — raw material from the dialogue, distributed into sections later

Head field roles:
- Title: identity (also slug, URL, exact-match anchor)
- Tags: facets (status, area, subsystem, thread)
- Summary: prose context, agent-readable

Body:
- Presence is known to the skill — take-note.sh accepts body on stdin and writes it.
- Structure is silent — the skill prescribes no body template. The agent decides shape from context and intent.

Triggers:
- 1. User explicitly asks (default).
- 2. Agent offers when a new discovery is made; user approves or denies (default).
- 3. User-requested auto-capture of new discoveries (opt-in).

Duplicate hygiene (dedup before writing):
- Before writing, agent checks for an existing note on the topic.
- Same topic: update or edit the existing note in place.
- Adjacent topic: write a new note and co-reference. Adjacent is not the same.
- Existing note already covers the content with nothing new to add: surface "there's already a note on this topic" instead of writing a duplicate.
- Critical judgment: avoid information loss. User-requested change can mutate freely; agent-initiated change must be additive. Don't overwrite without being asked.

Sibling co-reference:
- Siblings — notes on related topics within the same thread — share a tag.
- The shared tag is a slug of the thread or topic, derived via plugins/skills/scripts/slugify.sh.
- Tag membership lets scan.sh --tag <tag> retrieve the whole thread.

Document graph:
- Notes form a graph: nodes = notes, edges = shared tag membership.
- Multi-tag notes belong to multiple subgraphs simultaneously.
- Tag-filtered scans (scan.sh --tag <tag>) project a single subgraph.

Tag discipline:
- Ad-hoc per note; no controlled vocabulary.
- User often signals content type in the request ("add a todo note", "add a discovery note"); the agent picks tags from intent and topic.
- Lightly-typed convention; prescription unnecessary.

Title discipline:
- Names the topic explicitly; concrete over abstract.
- User may specify the title; otherwise the agent derives it from topic, content, and conversation.
- General English composition guidance comes from writing-prose (concrete-over-abstract, front-load-important-words, action-oriented-headings) — taking-notes inherits, does not re-prescribe.
- Taking-notes-specific: title is also identity, slug, URL, and search anchor — make it discriminating enough that exact-match and slug derivation give a useful result.
- When a question note gets its answer, the title may pivot from interrogative to declarative. The same note evolves; renaming the title regenerates the slug via take-note.sh.

Summary discipline:
- One sentence; front-loads the most informative phrase.
- Names what's in the note that title and tags don't already convey.
- Distinguishes it from siblings sharing the same tag.
- Uses words a future searcher would type.
- Skips meta-framing ("this note discusses...").
- General editorial guidance (active voice, concrete, no hedges) inherited from writing-prose.

Lifecycle:
- Out of scope. Lifecycle is managed externally.

Audience:
- Both agent and user read bodies.
- Content optimization leans toward LLMs — dense, structured, scannable signal over human-prose flourishes.

Agent's response to a write:
- The file stands as the artifact; no recital or recap in chat.
- Agent confirms with a minimal acknowledgment: "note written here: {slug}.md".

Read flow:
- Agent consults notes when it decides it needs context (autonomous).
- User may @-reference a specific note to include it in the conversation.

Trigger 2 — what counts as a discovery worth offering for:
- Resolving an open question that was in conversation context.
- Uncovering the connection between two previously-unconnected ideas.
- Comprehending a mechanism for the first time.
- Decomposing an idea — unpacking a complex notion into parts.
- Composing an idea — packing related ideas into a unified concept.
- A negative result — a dead end, a ruled-out approach, an experiment that failed.
- An open question crystallizing — what is unknown becomes precise enough to write down even before it has an answer.
- Shared signal: a new graph connection between concepts.

Trigger 3 — auto-capture mode:
- Same signal set as trigger 2; the user-approval gate is skipped.
- Activated as a mode the user puts the agent into.

Note format:
- Notes live under docs/notes/ at the repo root.
- Filename is <slug>.md. Slug rule: title lowercased, non-alphanumerics replaced with dashes, runs of dashes collapsed, leading/trailing dashes trimmed, capped at 80 characters. The slug is mechanically derived from the title — never hand-edited. Renaming a note means changing the title and regenerating the file via take-note.sh.
- The head is owned by take-note.sh. The script composes H1, blank line, Tags: line, and summary line from its arguments. The agent supplies <title>, <tags>, and <summary> as args; the script lays them out.
- The body is everything piped on stdin. Body has H2 sections; titles and contents are the agent's choice (OIN is one option among many).
- References between notes: plain text (see {slug}.md) inline; never markdown links. Notes live on web and on disk; links break across contexts.

Template (what take-note.sh produces):
```
# <one-line title — the H1>

Tags: <comma-separated, optional>
<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```

Trigger phrases vs. trigger behaviors:
- Legacy `### When to write a note` is a list of trigger phrases ("write this down", "save this for later", "open question:"). That belongs in the frontmatter `description:` per Anthropic guidance — phrases that activate the skill.
- Our three triggers (user asks; agent offers on discovery signal; auto-capture mode) are signal + judgment behaviors. Those belong in the skill body because they require the agent to apply judgment.
- Legacy `### When not to write a note` is similar — anti-conditions for activation, belongs adjacent to the trigger phrases in `description:`.

Memory vs. notes:
- Notes: any topic related to this repo — its plugins, skills, scripts, structure, design.
- Memory: cross-repo facts, user profile, persistent preferences. Anything that spans repos and sessions.
- Subject decides routing, not the trigger phrase.

Don't take a note when:
- The authoritative source (code, CLAUDE.md, git history) already says it — link to the source instead.
- The content is conversational ephemera — recap of what was just said, transcript of what was tried. Capture the durable finding, not the path to it.

Label speculation:
- A guess stated as fact is misinformation aimed at future self. The labels are the contract.
- Label what is observed, what is inferred, and what is guessed — never let the labels blur. "Maybe X" or "Hypothesis: X" is fine; an unlabeled guess passes as a verified fact.

Observation before interpretation:
- When capturing an investigation, record observable facts before the meaning assigned to them. "Endpoint returned 503 at 14:22" is observation; "the service is overloaded" is interpretation.
- Conflating the two poisons later analysis — the interpretation gets cited as if it were the measurement.
- Two separate sentences, or two separate sections, keep the boundary visible.

Why head hygiene matters:
- Notes earn their value from the graph. Tags define subgraph membership; titles are identity nodes; the scanner reads the head. Title, tag, and summary hygiene maintains the graph; when hygiene slips, retrieval degrades and the graph stops being useful.

Well-formed notes (defect rules — fix when violated):
- A note without a one-line summary in the head is a defect. The summary is what the scanner reads.
- A note whose body restates the summary verbatim is a defect. The summary is the head; the body is the evidence and reasoning.
- A note whose title and slug disagree (manual rename without regenerating the slug) is a defect. The title and the filename are one fact in two places; they agree.
- A note that covers two topics is a defect. Split it.
- A note that duplicates an existing note is a defect. Merge them.

Intentionally omitted (don't re-introduce):
- "No -v2.md files, no superseded markers in body" — git history is the authoritative version trace; defect rules don't need to legislate it.
- Dangling references to non-existent slugs — don't tell the agent it's okay; silence keeps it from happening.

Script operations (signature + output discipline, one section):
- The scripts under ${CLAUDE_PLUGIN_ROOT}/skills/taking-notes/scripts/ are the agent's interface to the note set. Composition, enumeration, and retrieval go through them so the head structure stays uniform and the document graph stays scannable.
- take-note.sh [--force] <title> <tags> <summary> — body piped on stdin. Slugifies the title, refuses to overwrite without --force, writes docs/notes/<slug>.md. Success is silent (file is the artifact); failure prints validation error to stderr and exits non-zero.
- scan.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT] — emits head blocks for every docs/notes/*.md (title, tags, summary, filename). Each flag is an optional predicate; flags AND together. No predicates lists every note. Title and summary match substring case-insensitive; --tag exact-match within the comma-separated Tags: line; --xtag excludes. Empty docs/notes/ prints "no notes"; predicates that match nothing print "no notes matching <predicates>". Exit 0 either way — a clean empty result is success.

=== Intro material (for didactic meta-discourse — not a body principle) ===

- Notes externalize knowledge to survive compaction. Conversation context evaporates; the file persists.
- What persists is the durable finding, not the transcript that produced it.
- Load writing-prose before composing notes. This skill specializes the rhetorical context that writing-prose declares; the foundation must be in context for the override semantics to apply.

[more facts added as the dialogue progresses]
-->

## Philosophy

Notes are the durable layer beneath the conversation. The conversation compacts; the notes do not. The next session reads what this one wrote.

Notes represent the current state of an idea; the journal tells the story of how we got there. The two artifacts are siblings — a wiki page and an engineering notebook — and the taking-notes skill produces only the former. The journal — dated entries, append-only, ordered by time — is a separate skill with a separate shape.

### Externalize to survive compaction

A fact that lives only in the conversation evaporates the moment the context window does. The note is the persistence layer. Anything worth remembering past the next compaction — a hypothesis, a measurement, a dead end, a decision, a reference — is worth a note.

### One topic per note

Each note covers one topic. The title names it; the slug is the file. Two topics get two notes, linked. Stuffing a second topic into an existing note breaks dedup, breaks scan, and breaks the link graph — the second topic has no title of its own and cannot be found by it.

### Title is identity

The title is what the note is, not what it is about. "Cache TTL is 300s" is a title; "Cache investigation" is a topic header pretending to be a title. The slug derives from the title, so the title is also the URL. Renaming the title means renaming the file and updating inbound links; treat it like renaming a function.

### Observation before interpretation

Record the observable fact before the meaning assigned to it. "Endpoint returned 503 at 14:22" is observation; "the service is overloaded" is interpretation. Conflating them poisons later analysis — the interpretation gets cited as if it were the measurement. Two separate sentences, often two separate sections, keep the boundary visible.

### Label speculation

A hypothesis stated as fact is misinformation aimed at future self. The note labels what is observed, what is inferred, and what is guessed — and never lets the labels blur. "Maybe the cache is stale" belongs in an Interpretation section or under a "Hypothesis:" prefix; "the cache TTL is 300s per config" belongs in Observation. The labels are the contract.

### Negative results are notes

A dead end documented prevents the dead end being repeated. The next session, or the same session after compaction, does not see the reasoning that ruled out an approach — only the conclusion. Writing "tried X, did not work because Y" is the cheapest insurance against doing X again next week. A note titled for the dead end is as legitimate as a note titled for the answer.

### Open questions are notes too

A question that goes unrecorded gets re-asked next session. Writing it down — even with no answer yet — captures what is unknown, why it matters, and what would resolve it. The note's title states the question; the body holds partial knowledge and the path toward an answer. Discoveries and questions are peers: the discovery says "here is what is known," the question says "here is what is not known yet." When the answer arrives, the same note evolves to record it; the title may pivot from interrogative to declarative.

### Link liberally

Wiki notes earn their value from the graph. When a note references a concept that has — or could have — its own page, link to it. A dangling link to a page that does not yet exist is a feature, not a defect: it marks the topic as worth a page when the next session has the context to write one.

### Always the latest state; git is the history

Notes are totally mutable. A note represents the current understanding of its topic — not a record of prior belief. When the understanding changes, the note changes; the old text goes away. No "previously we thought X" sections, no `-v2.md` companion files, no superseded markers. The revision history lives in git. A new file is for a new topic; the same file evolves to reflect the current truth about its own topic.

### The note is the artifact

Once the note is written, the work of recording is done. The chat does not recite the note back; the file under `docs/notes/` is the deliverable.
