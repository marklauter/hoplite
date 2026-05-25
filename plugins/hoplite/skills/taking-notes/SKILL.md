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

## Save the file — path and template

Notes are saved at `docs/notes/<slug>.md` where `<slug>` is a lowercase slug of the H1 title. Glob the target path first to learn whether the note exists. For a new note, use Write. For an existing note, use Edit to extend the body — adding content needs no approval. Removing content, or replacing the file wholesale, requires user approval. After saving, confirm with a minimal acknowledgment — for example, `note saved: <slug>.md`. No recital or recap.

!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/template.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/title.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/summary.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/editorial-principles/body.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/hoplite/frontmatter.md`
!`cat ${CLAUDE_PLUGIN_ROOT}/components/hoplite/tool-reference.md`
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
