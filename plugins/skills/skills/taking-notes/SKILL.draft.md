---
name: taking-notes
description: Use when the user asks to write something down, save something for later, record something, take a note, or capture an open question — or when a discovery worth preserving emerges in conversation. Composes on writing-prose; produces durable, structured notes under docs/notes/ retrieved via the script set.
---

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
- Tag membership lets list-notes.sh <tag> and query.sh --tag <tag> retrieve the whole thread.

Document graph:
- Notes form a graph: nodes = notes, edges = shared tag membership.
- Multi-tag notes belong to multiple subgraphs simultaneously.
- Tag-filtered scripts (list-notes.sh <tag>, query.sh --tag <tag>) project a single subgraph.

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
- list-notes.sh [<tag>] — emits head blocks for every docs/notes/*.md (title, tags, summary, filename). With a tag, filters to notes whose Tags: line contains that tag. Empty result prints "no notes"; tag filter with no matches prints an explanatory line.
- query.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT] — multi-predicate AND-scan. Title and summary match substring case-insensitive; --tag exact-match within the comma-separated Tags: line; --xtag excludes. Output mirrors list-notes.sh. Empty result prints "no matches"; exit 0 either way — a clean empty result is success.

=== Intro material (for didactic meta-discourse — not a body principle) ===

- Notes externalize knowledge to survive compaction. Conversation context evaporates; the file persists.
- What persists is the durable finding, not the transcript that produced it.
- Load writing-prose before composing notes. This skill specializes the rhetorical context that writing-prose declares; the foundation must be in context for the override semantics to apply.

[more facts added as the dialogue progresses]
-->

# Taking notes

A note is a durable, structured artifact stored in `docs/notes/`. Notes survive beyond the scope of short term memory and context windows. Anything worth remembering belongs in a note: a hypothesis, a measurement, a decision, an open question, a reference, and so on.

Ensure the companion skill, `writing-prose` is loaded before composing a note.

## Rhetorical context

- Writer: contributor
- Voice: declarative, terse
- Ethos: expert
- Stance: neutral
- Audience: a future reader picking up where this session left off — the same agent after compaction, a different agent in a later session, or the user revisiting
- Subject: any repo-scoped topic worth a durable record — discoveries, decisions, observations, open questions, dead ends, design fragments
- Genre: note
- Tone: professional, even-keeled
- Register: ADR — declarative, present-tense, mutable but always current; the note evolves as understanding does and replaces prior content rather than versioning it
- Intent: externalize repo-scoped findings into structured, retrievable artifacts that survive context compaction

## Note format

Notes live under `docs/notes/` at the repo root. The filename is `<slug>.md`. The slug is mechanically derived from the title: lowercased, non-alphanumerics replaced with dashes, runs of dashes collapsed, leading and trailing dashes trimmed, capped at 80 characters. The slug is never hand-edited; renaming a note means changing the title and regenerating the file via `take-note.sh`.

The head is owned by `take-note.sh`. The script composes the H1, blank line, `Tags:` line, and one-line summary from its arguments. The agent supplies `<title>`, `<tags>`, and `<summary>` as args; the script lays them out.

The body is everything piped on stdin. Body has H2 sections; titles and content are the agent's choice. Observation/Interpretation/Next is one shape that fits investigation notes; references, decisions, and todo notes take whatever shape fits the intent.

References between notes are plain text inline — `(see {slug}.md)`. Never markdown links: notes live on web and on disk, and links break across contexts.

The template `take-note.sh` produces:

```
# <one-line title — the H1>

Tags: <comma-separated, optional>
<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```

## Script operations

The scripts under `${CLAUDE_PLUGIN_ROOT}/skills/taking-notes/scripts/` are the agent's interface to the note set. Composition, enumeration, and retrieval go through them so the head structure stays uniform and the document graph stays scannable. Do not use Explore, Glob, or Grep against `docs/notes/`; the scripts are the canonical access mechanism.

- `take-note.sh [--force] <title> <tags> <summary>` — body piped on stdin. Slugifies the title, refuses to overwrite without `--force`, writes `docs/notes/<slug>.md`. Success is silent — the file is the artifact. Failure prints the validation error to stderr and exits non-zero.
- `list-notes.sh [<tag>]` — emits one head block per `docs/notes/*.md` (title, tags, summary, filename). With a tag argument, filters to notes whose `Tags:` line contains that tag. Empty result prints `no notes`; tag filter with no matches prints an explanatory line.
- `query.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT]` — multi-predicate AND-scan. `--title` and `--summary` match substring case-insensitive; `--tag` matches exactly within the comma-separated `Tags:` line; `--xtag` excludes notes carrying the named tag. Output mirrors `list-notes.sh`. Empty result prints `no matches`; exit 0 either way — a clean empty result is success.

The agent consults notes when it decides it needs context. The user may `@`-reference a specific note to include it in the conversation. After writing a note, the agent confirms with a minimal acknowledgment — for example, `note written here: {slug}.md` — and lets the file stand. No recital or recap.

## Routing

Notes cover any topic related to this repo — its plugins, skills, scripts, structure, and design. Memory covers cross-repo facts, user profile, and persistent preferences — anything that spans repos and sessions. Subject decides routing, not the trigger phrase.

Do not write a note when:

- The authoritative source (code, CLAUDE.md, git history) already says it. Reference the source by stable identifier instead. Detail that is both discoverable elsewhere and prone to drift belongs at its source, not duplicated in the note.
- The content is conversational ephemera — recap of what was just said, transcript of what was tried. The note captures the durable finding, not the path to it.

## Triggers

Three behaviors write a note. Two are on by default; the third is opt-in.

1. **User asks.** The user requests a note; the agent writes one.
2. **Agent offers on a discovery.** When a discovery surfaces, the agent proposes a note; the user approves or denies before writing.
3. **Auto-capture mode.** The user puts the agent into a mode that captures discoveries without the approval gate.

A discovery worth offering a note for is a new graph connection between concepts: resolving an open question in conversation context, uncovering a connection between previously-unconnected ideas, comprehending a mechanism for the first time, unpacking a complex idea into parts, packing related ideas into a unified concept, ruling out a dead end, or crystallizing an unknown into a precise question.

## Duplicate hygiene

Before writing, scan for an existing note on the topic via `list-notes.sh` or `query.sh`.

- **Same topic exists.** Update or edit the existing note in place.
- **Adjacent topic exists.** Write a new note and co-reference. Adjacent is not the same.
- **Existing note covers the content with nothing to add.** Surface "there's already a note on this topic" instead of writing a duplicate.

Avoid information loss. User-requested change can mutate freely; agent-initiated change is additive. Don't overwrite without being asked.

## Head discipline

Three head fields carry the load: title, tags, summary. Each has its own discipline.

### Title

Names the topic explicitly. Concrete over abstract. The title is identity, slug, URL, and search anchor — discriminating enough that exact-match scan and slug derivation give a useful result. Title is what the note is, not what it is about.

When the user supplies a title, use it. Otherwise derive from topic, content, and conversation. General English composition guidance — concrete over abstract, front-load important words, action-oriented heading — comes from `writing-prose`.

When a question note gets its answer, the title may pivot from interrogative to declarative. The same note evolves; renaming the title regenerates the slug via `take-note.sh`.

### Tags

Tags are facets. Common dimensions: status (`todo`, `closed`), area (`skills`, `scripts`, `tests`), subsystem (`writing-prose`, `wiki`), thread (`audit-mode-followup`, `refactor`). No controlled vocabulary — the agent picks tags from topic and intent.

When the user signals content type in the request ("add a todo note", "add a discovery note"), the named type becomes a tag. Multi-tag membership is the norm; a note may belong to several subgraphs simultaneously.

Sibling notes — notes on the same thread — share a tag. The shared tag is the thread slug, derived via `${CLAUDE_PLUGIN_ROOT}/scripts/slugify.sh`. Tag membership lets `list-notes.sh <tag>` and `query.sh --tag <tag>` retrieve the whole thread.

### Summary

One sentence. Front-load the most informative phrase. Name what's in the note that title and tags don't already convey. Distinguish it from siblings sharing the same tag. Use words a future searcher would type. Skip meta-framing ("this note discusses..."). General editorial guidance — active voice, concrete, no hedges — comes from `writing-prose`.

## Body principles

The skill prescribes no body template. Section titles and content are the agent's choice given the note's intent. Two disciplines apply to body content regardless of shape.

### Label speculation

A guess stated as fact is misinformation aimed at future self. The labels are the contract. Label what is observed, what is inferred, and what is guessed — never let the labels blur. "Maybe X" or "Hypothesis: X" is fine; an unlabeled guess passes as a verified fact.

### Observation before interpretation

When capturing an investigation, record observable facts before the meaning assigned to them. Conflating the two poisons later analysis — the interpretation gets cited as if it were the measurement. Two separate sentences, or two separate sections, keep the boundary visible.

## Well-formed notes

Notes earn their value from the graph. Tags define subgraph membership; titles are identity nodes; the scanner reads the head. Title, tag, and summary hygiene maintains the graph; when hygiene slips, retrieval degrades and the graph stops being useful. When a note is malformed, the rule is: fix it.

Defects:

- A note without a one-line summary in the head. The summary is what the scanner reads.
- A note whose body restates the summary verbatim. The summary is the head; the body is the evidence and reasoning.
- A note whose title and slug disagree. The title and the filename are one fact in two places; they agree.
- A note that covers two topics. Split it.
- A note that duplicates an existing note. Merge them.
