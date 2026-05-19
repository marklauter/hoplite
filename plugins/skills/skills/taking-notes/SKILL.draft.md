---
name: taking-notes
description: <TBD — refine after composition/retrieval design settles>
---

# Taking notes

<!-- design scratch — raw material from the dialogue, distributed into sections later

Head field roles:
- Title: identity (also slug, URL, exact-match anchor)
- Tags: facets (status, area, subsystem, thread)
- Summary: prose context, agent-readable

Scope boundary (for our discovery, not skill content):
- Out of scope: dated session logs / engineering journals (separate journaling skill).
- Taking-notes covers notes — durable, structured header, retrievable, indexed via the script set.

Body:
- Presence is known to the skill — take-note.sh accepts body on stdin and writes it.
- Structure is silent — the skill prescribes no body template. The agent decides shape from context and intent.

Triggers:
- 1. User explicitly asks (default).
- 2. Agent offers when a new discovery is made; user approves or denies (default).
- 3. User-requested auto-capture of new discoveries (opt-in).

Dedup and mutation:
- Before writing, agent checks for an existing note on the topic.
- If one exists: agent may update/edit, or compose a sibling and co-reference.
- Critical judgment: avoid information loss.
- User-requested change can mutate freely; agent-initiated change must be additive.
- General rule: don't overwrite without being asked.
- If an existing note already covers the topic and adds nothing new, surface "there's already a note on this topic" instead of writing.

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
- Shared signal: a new graph connection between concepts.

Trigger 3 — auto-capture mode:
- Same signal set as trigger 2; the user-approval gate is skipped.
- Activated as a mode the user puts the agent into.

Note template (shape):
- Head is fixed by take-note.sh — H1 from <title>, blank, Tags: line, summary line.
- Body has H2 sections; titles and contents are the agent's choice (OIN is one option among many).

Template:
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

[more facts added as the dialogue progresses]
-->

<intro: didactic meta-discourse — TBD>

## Rhetorical context

<TBD — slot declarations per writing-prose contract>

## Composition

<TBD>

## Retrieval

<TBD — anchors the script set as fixed contract>
