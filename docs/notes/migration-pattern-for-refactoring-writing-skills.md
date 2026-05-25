---
title: Migration pattern for refactoring writing skills
summary: Transformation function for moving a legacy Philosophy/Guidance/Validation skill into the new foundation-composition + procedural-OODA shape; derived from the taking-notes refactor and reusable for journaling and other downstream skills.
tags: [refactor, skills, writing-prose, migration, pattern]
created: 2026-05-25
aliases: []
---

## Before and after

- Legacy: `plugins/armory/skills/taking-notes/SKILL.old.md` — the input to this transformation.
- Refactored: `plugins/armory/skills/taking-notes/SKILL.md` — the output.

## Input: legacy shape

Legacy skills follow a Philosophy / Guidance / Validation (PGV) structure:

- Frontmatter: name, description with trigger phrases
- Intro: descriptive prose about the artifact
- ## Philosophy: principles, often with ### named-anchor subsections, sometimes with concrete examples ("Cache TTL is 300s")
- ## Guidance: concrete patterns (location, template, when-to/when-not-to, dedup, linking)
- ## Validation: script set, output discipline, gate policies

Often present: bold for emphasis, OIN template as default body shape, "wiki" framing, gratuitous citations (Drucker), portability claims, dangling-link permissions.

## Output: new shape

New skills compose on writing-prose and follow a procedural-OODA + reference shape:

- Frontmatter: name + description (description carries trigger phrases per Anthropic guidance)
- # H1 + bare-concept intro (didactic meta-discourse): what the artifact IS, what survives, load-foundation instruction, n-step process preview
- Procedural H2 sections, one per process step (for taking-notes: Spot the trigger -> Search for existing -> Compose the note -> Record the note)
- Reference H2 sections (script references with signature blocks, conceptual model section, artifact format)
- ## Rhetorical context section (slots; placement is flexible — taking-notes put it last)

Structural conventions: no bold, em-dashes for parentheticals, sentence-case headings, full `${CLAUDE_PLUGIN_ROOT}/...` path in signature blocks (prefixed with `bash`), intra-doc links by GFM anchor, overloaded verbs disambiguated (compose / save / record).

## Preservation contract

Structural tightening is lossless on ideas. Cut prose, tighten layout, deduplicate — but every load-bearing claim from the legacy must survive the refactor. Ideas leave only by judgment: bad claims, abandoned framings, or content already covered by the foundation. Track intentional omissions; everything else carries over to its natural home in the new shape. The taking-notes before/after pair (`SKILL.old.md` and `SKILL.md`) is the worked record of which decisions excluded which legacy ideas.

## Transformation steps

1. Identify the artifact's process — the OODA loop. For taking-notes: spot trigger -> search dedup -> compose content -> save via script. Each step becomes an H2.
2. Draft the bare-concept intro. Direct, non-flowery. "A note is a durable, structured artifact stored in `docs/notes/`." Then survives-compaction, foundation-load instruction, n-step preview.
3. Declare Rhetorical context with all ten slots. Subject and intent required. Declare overrides explicitly; use bare values (no "(default)" / "(override)" annotations). Use natural language; avoid borrowed register names that don't fit.
4. Build the script-reference sections with a consistent shape: prose intro -> `bash script.sh` name + one-line description -> Signature fence with full `${CLAUDE_PLUGIN_ROOT}/...` path -> flag/mode bullets -> output paragraph.
5. Build the conceptual-model section if the artifact set has structure beyond individual files. For notes: the graph. For journal: likely the timeline. Tie scripts to the model.
6. Build the artifact-format section. Header/body split, template fence, head field disciplines (H3 or H4 subsections per field if rich enough).
7. Mine the legacy section by section. Classify each idea as captured, intentionally dropped, or lost. Re-introduce lost-but-important ideas at their natural home.
8. Sweep prose for: writing-prose violations (bold, hedge words, Latin abbreviations, hyphens that should be em-dashes), overloaded verbs, missing path qualification, stale anchor links.
9. Run tests against any renamed/changed scripts.
10. Cut over draft -> live SKILL.md.

## Per-step rationale (with taking-notes examples)

**Step 1 (OODA loop):** The 4 steps came from re-deriving the workflow from first principles in dialogue. The intro sentence "Recording a note has four steps: spot the trigger, search for an existing note on the topic, compose the content, and record the note." became the navigation hook for the four step H2s.

**Step 2 (bare-concept intro):** Avoid "Note-authoring knowledge..." (positions the skill, not the artifact). Use "A note is..." (positions the artifact directly).

**Step 3 (Rhetorical context):** For taking-notes, register was hard — no catalog entry fit. Declared inline: "declarative, present-tense, mutable and always current; the note evolves as understanding does and replaces prior content rather than versioning it." Audience required animacy fix: "a future reader picking up where this session left off" (sessions are not animate; future readers are).

**Step 4 (script-reference shape):** Both record-note.sh and scan.sh follow: short intro -> name + role -> Signature fence -> flags/modes -> output. Full `${CLAUDE_PLUGIN_ROOT}/...` path in the signature only; bare names elsewhere. `bash` prefix in the signature reinforces the invocation convention.

**Step 5 (conceptual model):** "Notes form a graph" as bipartite — notes are concrete nodes, tags are virtual nodes (meta-topics). When a tag value matches a slug, the virtual node coincides with the concrete one. Ties scan.sh and record-note.sh to a unified mental model.

**Step 6 (artifact format):** Header bullet + Body bullet, then template fence. Head field discipline as H3 with H4 subsections per field (Title, Tags, Summary). Body principles as separate H3.

**Step 7 (mine legacy):** Walked the legacy section by section, classified each idea as captured / intentionally dropped / lost. Re-introduced lost-but-important ideas (e.g., dead-end rationale folded into trigger 2, one-topic rationale as Compose section lede).

**Step 8 (prose sweep):** Stripped 11 instances of bold. Replaced hyphens with em-dashes in H3 subtitles. Disambiguated overloaded verbs: **compose** (arrange words), **save** (push to disk), **record** (full act); kept `writing-prose` (skill name), `Writer:` (slot), `overwrite` (precise verb).

## Pitfalls and decisions

- Register catalog names that don't fit the artifact: don't borrow. Declare inline. The "Note" register in writing-prose's catalog is for ephemeral scratch; taking-notes notes are durable.
- "wiki" framing is overloaded. Drop. Use the artifact name directly ("note").
- Hierarchy nesting depth: H4 is OK for disciplines under a wrapper H3; deeper gets unscannable.
- Bold-as-emphasis violates writing-prose. Use prose flow instead.
- Examples that depend on shared session context ("Cache TTL is 300s") don't translate to the agent reader. State rules directly.
- Lifecycle (when artifacts get closed/deleted): intentionally out of scope. Silence is the right disposition.
- Dangling-link permission: intentionally omitted to avoid encouraging dangling links.
- The intra-doc anchor for headings with em-dashes is GFM-derived and may need verification in a renderer.

## Open questions for journaling

- The journaling OODA loop will likely differ. Probably: observe-session -> compose-entry -> save. Possibly no dedup, since journal entries are append-only chronological.
- Register may fit "Journal" from the writing-prose catalog directly (observation-based, chronological, append-only, first-person acceptable). Verify before declaring inline.
- Conceptual model: probably a timeline rather than a graph. May not need a peer "X form a Y" section if the timeline shape is obvious.
- Reference sections: journal-entry.sh, list-journal.sh, query.sh need the same signature/path treatment with `bash` prefix.
- Skill-composition note's "Direct instruction" and "Soft on procedure" principles apply equally.
- Memory vs journal routing rule analogous to memory vs notes — but journal scope differs (per-session vs durable wiki note).
