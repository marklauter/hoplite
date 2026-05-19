---
name: taking-notes
description: Use when the user asks to write something down, save something for later, record something, take a note, or capture an open question — or when a discovery worth preserving emerges in conversation. Composes on writing-prose; produces durable, structured notes under docs/notes/ retrieved via the script set.
---

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
- Register: declarative, present-tense, mutable and always current; the note evolves as understanding does and replaces prior content rather than versioning it
- Intent: externalize repo-scoped findings into structured, retrievable artifacts that survive context compaction

## Recording a note

1. when to record a note
2. check for existing note
3. how to record the note (before the note format)

### When to record a note

You record a note when one of three things happens:

1. **The user asks.** They request a note; you write one.
2. **A discovery surfaces.** A new graph connection between concepts: resolving an open question in conversation context, uncovering a connection between previously-unconnected ideas, comprehending a mechanism for the first time, unpacking a complex idea into parts, packing related ideas into a unified concept, ruling out a dead end, or crystallizing an unknown into a precise question. You propose a note; the user approves or denies before you write.
3. **Auto-capture mode is on.** The user has asked you to auto-capture discoveries without the approval gate; discovery signals are the same as #2.

Notes may cover any topic related to host repo. Memory covers cross-repo facts, user profile, and persistent preferences — anything that spans repos and sessions. Subject and topic determine routing, not the trigger phrase.

Exclude from notes:

- Discoverable content — anything the authoritative source (code, CLAUDE.md, git history, other notes, directory structure) already states. Reference by stable identifier; duplication drifts as the source changes.
- Conversational ephemera — recap of what was just said, transcript of what was tried. Capture the durable finding, not the path to it.

### Check for an existing note

Before writing, scan for an existing note on the topic via [`scan.sh`](#scanning-finding-and-reading-notes).

- **Same topic exists.** Update or edit the existing note in place.
- **Adjacent topic exists.** Write a new note and co-reference (see [Tags](#tags)).
- **Existing note covers the content with nothing to add.** Surface "there's already a note on this topic" instead of writing a duplicate.

Avoid information loss. User-requested change can mutate freely; agent-initiated change is additive. Don't overwrite without being asked or securing user approval.

### Note format

Notes live under `docs/notes/` at the repo root. The filename is `<slug>.md`.

A note has two parts: a four-line header and a content body.

The header is: H1 title line, blank line, `Tags:` line (comma-separated), one-line summary.

The filename and header are owned by [`record-note.sh`](#write-the-file). You supply `<title>`, `<tags>`, and `<summary>` as arguments; the script slugifies the title into the filename and composes the four header lines. The slug is never hand-edited; renaming a note means changing the title and regenerating the file via `record-note.sh`.

The body is everything you pipe on stdin. Body has H2 sections; titles and content are yours to choose. Observation/Interpretation/Next is one shape that fits investigation notes; references, decisions, and todo notes take whatever shape fits the intent.

References between notes are plain text inline — `(see {slug}.md)`. Never markdown links: notes live on web and on disk, and links break across contexts.

The template `record-note.sh` produces:

```
# <one-line title — the H1>

Tags: <comma-separated, optional>
<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```

### Title

Name the topic explicitly. Concrete over abstract. The title is identity, slug, URL, and search anchor — discriminating enough that exact-match scan and slug derivation give a useful result. Title is what the note is, not what it is about.

When the user supplies a title, use it. Otherwise derive from topic, content, and conversation. General English composition guidance — concrete over abstract, front-load important words, action-oriented heading — comes from `writing-prose`.

When a question note gets its answer, the title may pivot from interrogative to declarative. The same note evolves; renaming the title regenerates the slug via `record-note.sh`.

### Tags

Tags are facets. Common dimensions: status (`todo`, `closed`), area (`skills`, `scripts`, `tests`), subsystem (`writing-prose`, `wiki`), thread (`audit-mode-followup`, `refactor`). No controlled vocabulary — pick tags from topic and intent.

When the user signals content type in the request ("add a todo note", "add a discovery note"), the named type becomes a tag. Multi-tag membership is the norm; a note may belong to several subgraphs simultaneously.

Sibling notes — notes on the same thread — share a tag. The shared tag is the thread slug, derived via `${CLAUDE_PLUGIN_ROOT}/scripts/slugify.sh`. Tag membership lets `scan.sh --tag <tag>` retrieve the whole thread.

### Summary

One sentence. Front-load the most informative phrase. Name what's in the note that title and tags don't already convey. Distinguish it from siblings sharing the same tag. Use words a future searcher would type. Skip meta-framing ("this note discusses..."). General editorial guidance — active voice, concrete, no hedges — comes from `writing-prose`.

### Body principles

The skill prescribes no body template. Section titles and content are yours to choose given the note's intent. Two disciplines apply regardless of shape.

**Label speculation.** A guess stated as fact is misinformation aimed at future self. The labels are the contract. Label what is observed, what is inferred, and what is guessed — never let the labels blur. "Maybe X" or "Hypothesis: X" is fine; an unlabeled guess passes as a verified fact.

**Observation before interpretation.** When capturing an investigation, record observable facts before the meaning assigned to them. Conflating the two poisons later analysis — the interpretation gets cited as if it were the measurement. Two separate sentences, or two separate sections, keep the boundary visible.

### Write the file

Call `record-note.sh [--force] <title> <tags> <summary>` with the body piped on stdin. The script slugifies the title, refuses to overwrite without `--force`, and writes `docs/notes/<slug>.md`. Success is silent — the file is the artifact. Failure prints the validation error to stderr and exits non-zero.

After writing, confirm with a minimal acknowledgment — for example, `note written here: {slug}.md` — and let the file stand. No recital or recap.

### Well-formed notes

Notes earn their value from the graph. Tags define subgraph membership; titles are identity nodes; the scanner reads the header. Title, tag, and summary hygiene maintains the graph; when hygiene slips, retrieval degrades. When a note is malformed, the rule is: fix it.

Defects:

- A note without a one-line summary in the header. The summary is what the scanner reads.
- A note whose body restates the summary verbatim. The summary is the header; the body is the evidence and reasoning.
- A note whose title and slug disagree. The title and the filename are one fact in two places; they agree.
- A note that covers two topics. Split it.
- A note that duplicates an existing note. Merge them.

## Scanning, finding, and reading notes

You read notes when you decide you need context — to recover state from a previous session, look up a decision, or pull in sibling notes on a thread. The user may `@`-reference a specific note to include it in the conversation.

To find or read notes, use the script set. Do not use Explore, Glob, or Grep against `docs/notes/`; the scripts are the canonical access mechanism and emit the structured header fields you need.

- `scan.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT]` — emits one header block per `docs/notes/*.md` (title, tags, summary, filename). Each flag is an optional predicate; flags AND together. No predicates lists every note. `--title` and `--summary` match substring case-insensitive; `--tag` matches exactly within the comma-separated `Tags:` line; `--xtag` excludes notes carrying the named tag. Empty `docs/notes/` prints `no notes`; predicates that match nothing print `no notes matching <predicates>`. Exit 0 either way — a clean empty result is success.

The output of `scan.sh` is the card catalog. Use it to decide which notes to open. Open a note by reading the file at `docs/notes/<slug>.md`.
