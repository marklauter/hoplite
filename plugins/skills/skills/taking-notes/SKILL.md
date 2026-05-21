---
name: taking-notes
description: Use when the user asks to write something down, save something for later, record something, take a note, or capture an open question — or when a discovery worth preserving emerges in conversation. Notes go under docs/notes/.
---

# Taking notes

A note is a durable, structured artifact stored in `docs/notes/`. Notes survive beyond short-term memory and context windows. Anything worth remembering belongs in a note: a hypothesis, a measurement, a decision, an open question, a reference, and so on.

Recording a note has four steps: spot the note-invocation trigger, search for an existing note on the topic, compose the content, and record the note.

## Spot the trigger — when to record a note

Record a note when:

1. The user asks. They request a note; you compose one.
2. A discovery surfaces. A new graph connection between concepts: resolving an open question in conversation context, uncovering a connection between previously-unconnected ideas, comprehending a mechanism for the first time, unpacking a complex idea into parts, packing related ideas into a unified concept, or crystallizing an unknown into a precise question. You propose a note; the user approves or denies before you compose. Recording a dead end prevents repeating it.
3. Auto-capture mode is on. The user has asked you to auto-capture discoveries without the approval gate; discovery signals are the same as #2.

## Search for an existing note — duplicate hygiene

Before recording, scan for an existing note on the topic via `scan.sh`.

- Same topic exists. Use `record-note.sh --overwrite` to replace the note, or `--append` to extend the body in place (header is preserved).
- Adjacent topic exists. Compose a new note and co-reference (see [Tags](#tags)).
- Existing note covers the content with nothing to add. Surface "there's already a note on this topic" instead of recording a duplicate.

Preserve content. User-requested change mutates freely; agent-initiated change is additive — overwrite only on request or approval.

## Compose the note — topics and exclusions

Notes are repo-scoped; cross-repo facts, user profile, and persistent preferences belong in memory.

Each note covers one topic. Two topics get two notes — stuffing both into one breaks dedup and search.

Exclude from notes:

- Discoverable content — anything the authoritative source (code, CLAUDE.md, git history, other notes, directory structure) already states. Reference by stable identifier; duplication drifts as the source changes.
- Conversational ephemera — recap of what was just said, transcript of what was tried. Capture the durable finding, not the path to it.

## Record the note — record-note.sh reference

To record a note, use `record-note.sh`. The script slugifies the title and saves `docs/notes/<slug>.md`. After saving, confirm with a minimal acknowledgment — for example, `note saved: {slug}.md`. No recital or recap.

`record-note.sh` — save or extend a note.

Signature:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/taking-notes/scripts/record-note.sh [--overwrite | --append] <title> [<tags> <summary>]
```

Three modes (mutually exclusive):

- (no flag) — new note. Refuses to save if the target file exists.
- `--overwrite` — replace an existing note's full content (header + body).
- `--append` — extend an existing note's body. Header is preserved; pass only `<title>` to derive the slug.

Body is read from stdin and appended verbatim. Output: success is silent — the file is the artifact. Failure prints the validation error to stderr and exits non-zero.

## Finding notes — scan.sh reference

`scan.sh` is the canonical access mechanism for finding notes — it emits the structured header fields Explore, Glob, and Grep skip.

`scan.sh` — list and filter notes by structured predicates.

Signature:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/taking-notes/scripts/scan.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT]
```

Each flag is optional; flags AND together. No predicates lists every note.

- `--title PAT` — substring match, case-insensitive, against the H1 title
- `--tag TAG` — exact match against an entry in the comma-separated `tags:` line
- `--xtag TAG` — exclude notes whose `tags:` line contains TAG
- `--summary PAT` — substring match, case-insensitive, against the one-line summary

Output: one header block per match — title, tags, summary, filename. Empty `docs/notes/` prints `no notes`; predicates that match nothing print `no notes matching <predicates>`. Exit code 0 either way — clean empty result is success.

## Notes form a graph

Notes are nodes; tags are virtual nodes — meta-topics. A note connects to each tag in its `tags:` line; multiple notes carrying the same tag converge at that tag-node, forming a thread (subgraph). When a tag's value matches another note's slug, the virtual tag-node coincides with that concrete note. In that case, the tag is a direct edge to that note. The script set is the agent's interface to the graph: `record-note.sh` adds a note and its tag-connections; `scan.sh --tag <tag>` projects the subgraph around a tag-node.

## Note format

A note has two parts:

- Header — H1 title, blank line, `tags:` line (comma-separated), one-line summary. Composed by `record-note.sh` from its args.
- Body — H2 sections; titles and content are yours.

The template `record-note.sh` produces:

```
# <one-line title — the H1>

tags: <comma-separated, optional>
<one-line summary>

## <a section title>
<content>

## <another section title>
<more content>
```

### Head field discipline

Three head fields carry the discovery load: title, tags, summary.

#### Title

Name the topic explicitly. Concrete over abstract. Title is what the note is, not what it is about. Make it discriminating enough that exact-match scan returns the right note.

When the user supplies a title, use it. Otherwise derive from topic, content, and conversation.

When a question note gets its answer, the title may pivot from interrogative to declarative. Record the answered note under the new title and remove the old file.

#### Tags

Tags are facets that distill the note's content or intent. Common dimensions: status (`todo`, `closed`), area (`skills`, `scripts`, `tests`), subsystem (`writing-prose`, `wiki`), thread (`audit-mode-followup`, `refactor`). No controlled vocabulary — pick from what the note covers.

When the user signals content type in the request ("add a todo note", "add a discovery note"), the named type becomes a tag. Multi-tag membership is the norm; a note may belong to several subgraphs simultaneously.

Sibling notes share a tag-node (see [Notes form a graph](#notes-form-a-graph)); `scan.sh --tag <tag>` retrieves the thread. Tagging a note with another note's slug creates a direct edge — `scan.sh --tag <slug>` finds every note that cites the target.

#### Summary

One sentence. Front-load the most informative phrase. Name what's in the note that title and tags don't already convey. Distinguish it from siblings sharing the same tag. Skip meta-framing ("this note discusses...").

### Body principles

Label speculation. A guess stated as fact is misinformation aimed at future self. Label what is observed, what is inferred, and what is guessed — never let the labels blur. "Maybe X" or "Hypothesis: X" is fine; an unlabeled guess passes as a verified fact.

Observation before interpretation. When capturing an investigation, record observable facts before the meaning assigned to them. Conflating the two poisons later analysis — the interpretation gets cited as if it were the measurement. Two separate sentences, or two separate sections, keep the boundary visible.

### Well-formed notes

Notes earn their value from the graph. Tags define subgraph membership; titles are identity nodes; the scanner reads the header. Title, tag, and summary hygiene preserves retrieval. Fix malformed notes.

Defects:

- A note without a one-line summary in the header. The summary is what the scanner reads.
- A note whose body restates the summary verbatim. The summary is the header; the body is the evidence and reasoning.
- A note whose title and slug disagree. The title and the filename are one fact in two places; they agree.
- A note that covers two topics. Split it.
- A note that duplicates an existing note. Merge them.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/editorial-principles.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`

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
