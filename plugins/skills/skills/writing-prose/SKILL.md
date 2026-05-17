---
name: writing-prose
description: Use when writing, refactoring, or composing prose for markdown-based artifacts. Covers editorial guidance for rhetorical context, density, structure, and formatting.
---

# Writing prose

Foundational editorial knowledge lives here — the authoring virtues that apply across all markdown-based artifacts. Downstream skills specify the rhetorical context for the artifact under composition — writer, voice, ethos, stance, audience, subject, genre, tone, register, intent. Downstream skills may override with justification.

## Composition — principles that hold across all artifacts

### Source is the authority

The document defers to the system it describes. Read the source — code, configuration, schema, behavior — before writing about it. When prose and source disagree, fix the prose. When a term, file path, or identifier changes, every document mentioning it goes stale; update them in the same change set.

### Match the surrounding register

A document inherits its register from its neighbors. The agent reads siblings before composing. With no siblings, the agent asks; without an answer, the default is authoritative-declarative-terse — the voice of a contributor who has thought the design through.

### Lead with what the reader needs

The first sentence of any page names what the page is for and what the reader gets from it. Usage and behavior come before architecture and internals. The conclusion comes before the justification. The reader who stops after the first paragraph still leaves with the right impression.

### Self-contained pages

Each page stands on its own. Link liberally to supporting concepts, but include enough context that a reader who follows zero links still understands the page. A page that requires the reader to chase three links before the first sentence makes sense is incomplete.

### Define by presence

Say what something is, then stop. The negative is implied. "The facilitator runs discovery across all three lenses" needs no "and not across two lenses." Constraints sometimes read more naturally as negatives — phrase the negative outcome as a positive label ("invalid outcome", not "not a valid outcome").

### State each idea once

Every fact has one authoritative location. Other pages link to it; they do not restate it. Within a page, the same rule applies — a paragraph that restates an adjacent paragraph is one too many.

### Every word must earn its place

Push for density. Cut hedges, filler, transitions that announce, sentences that restate the previous sentence. Every removed word raises the signal-to-noise ratio of what remains.

Use as many words as the meaning needs and no more. Clarity outranks brevity at the cut-line.

### Examples carry weight

A concrete example outweighs an abstract claim. One brief example per rule is enough, and only when the rule is not self-evident. "Use sentence-case headings" needs no example; converting a table to headings and bullets benefits from showing before and after.

### Forms are the schema

Every recurring artifact type has a canonical shape. An ADR has context, decision, and consequences. A finding has severity, location, principle. A note has a title and a body that represents the current state of the idea. The shape is the contract; the instance fills the shape.

When a structural skill exists for an artifact type, that skill owns the shape. This skill governs the prose inside the shape.

### Markdown is the wire format

Prose in the repo is markdown. Not HTML, not docx, not a wiki engine's bespoke markup. The format is human-readable in source, LLM-readable without a renderer, and diffable in git.

A document that requires a tool to read it drifts silently from the source it describes.

### The first page sets the pattern

The first instance of any page type teaches the next ten. Naming, structure, register, depth of detail — the patterns established on the first page become the patterns subsequent pages copy, intended or not. Invest disproportionate care in the first instance.

## Guidance — concrete application of philosophy

### Source is the authority

- Read the source before writing about it — the file, the function, the schema, the command output. Documenting from memory is the most common way prose drifts from reality.
- When the doc and the source disagree, fix the doc. Update prose, not behavior.
- On renames and refactors, grep the entire project for the old name or path before declaring the change done. Update every reference in the same change set.
- Cite source files with `path:line` notation when claiming a specific behavior. The citation is what makes the claim verifiable.

### Match the surrounding register

- Read the sibling documents in the target directory before composing. The siblings define the operating register.
- When no siblings exist, ask the user about audience and register. Save the answer in the document or in a directory-level hint file rather than re-asking next time.
- The named registers and their tells:
  - Tutorial — friendly, walks the reader through one task at a time, builds understanding in sequence, second person, present tense, imperative steps.
  - Reference — dry, dense, factual, organized for lookup rather than reading, declarative, third person where appropriate, exhaustive on the surface area it covers.
  - Vision or design — authoritative, declarative, position-taking, terse, explicit about what is open versus settled.
- The default register, in the absence of any signal, is authoritative-declarative-terse. The voice of a contributor who has thought the design through.

### Lead with what the reader needs

- Open with a lede — one or two sentences naming what the document is for and what the reader gets from reading it.
- Usage before internals. Public surface before architecture. How to do it before how it works.
- Conclusions before justifications. State the position, then explain. The reader who reads only the first paragraph still leaves with the right answer.

### Self-contained pages

- Include enough context for a reader who follows zero links to understand the page. The link is for the reader who wants depth, not the reader who wants the basics.
- Link to canonical definitions for shared terms; do not restate them inline. The page that defines the term owns the definition; other pages link.
- When a concept is genuinely page-specific, define it inline on its first use.

### Define by presence

- Phrase principles, guidance, and instructions as positive assertions. Say what to do, not what to avoid.
- When a constraint reads more naturally as a negative ("duplicates the API cannot catch"), name the negative outcome with a positive label or leave the natural negation in place.
- Reserve negative framing for governance and review contexts where the boundary itself is the point.

### State each idea once

- A fact has one home. Other pages link to that home rather than restating it.
- Inside a page, each paragraph carries one idea that has not appeared in earlier paragraphs.
- When two paragraphs say the same thing at different lengths, keep the one that says it best and delete the other.

### Every word must earn its place

- Cut hedges: *might*, *perhaps*, *could be*, *it's worth noting*, *might want to*.
- Cut filler: *basically*, *simply*, *just*, *actually*, *really*, *quite*, *very*, *in order to*.
- Cut transitions that announce instead of saying. "In this section we will discuss X" — say X.
- Replace wordy stock phrases with their short form: *at this point in time* → *now*, *due to the fact that* → *because*, *in the event that* → *if*.
- Write assertions, not commentary. Skip motivational framing and appeals to virtue; let each statement stand.
- Stop cutting when the shorter version asks the reader to reconstruct what the longer version said outright. Clarity outranks brevity at the cut-line.

### Examples carry weight

- One brief example per rule is enough, and only when the rule is not self-evident.
- Show the before and the after when the rule transforms shape (e.g., converting a table into headings and bullets):

  Before:

  ```markdown
  | Name | Purpose |
  |---|---|
  | foo | does X |
  | bar | does Y |
  ```

  After:

  ```markdown
  ### foo
  Does X.

  ### bar
  Does Y.
  ```

- Examples come after the rule, not before. The rule is the load-bearing claim; the example clarifies it.

### Forms are the schema

- When a structural skill exists for an artifact type, follow its shape without negotiation.
- When no structural skill yet exists and the artifact recurs, the first instance establishes the shape and a follow-up structural skill can codify it.
- Within the shape, this skill governs the prose. The shape is the schema; the prose is the instance.

### Markdown is the wire format

- All prose is markdown. Use standard markdown — headings, lists, code fences, links, em dashes, blockquotes.
- Use the em dash character (—) for parenthetical breaks, definitions, and appositives. Not double hyphens.
- Use the Oxford comma in lists of three or more — "nodes, edges, and memos."
- Code, paths, identifiers, and CLI commands go in backticks. Multi-line code samples go in fenced code blocks with the language tag.
- Links use `[text](path)` form. The link text describes what the target is, not "click here" or "this page."
- Sentence-case headings — only the first word and proper nouns capitalized.
- Numbered steps for procedures, bullets for unordered options, prose for reasoning.
- Skip bold. Headings, lists, and prose carry structure on their own; bold adds noise without changing how a reader (human or LLM) processes the text.
- Skip tables. Markdown tables are unreadable for humans in source form and add no value over headings and bullets.

### Terminology hygiene

- Capitalize defined role names in prose (User, Orchestrator, Reviewer). The capitalization signals that the term has a definition elsewhere.
- A domain term used meaningfully in multiple pages belongs in a glossary; link the first use in each page to the glossary entry.
- When a term's meaning differs between contexts, name the context: "the *user* of the CLI" vs "the *User* actor."

### The first page sets the pattern

- The first instance of any new artifact type or new section type gets extra review. The shape, naming, depth, and tone become the template the next instances copy.
- When deviating from an established pattern, name the deviation in the document and explain the reason briefly. Undocumented deviation teaches the next author to copy the wrong pattern.

## Validation — edit your own work before handing off

### The writing loop

1. Read the diff's surroundings — the sibling documents and the parent directory's tone. Confirm the register before judging your own prose.
2. Reread the changed prose against the Guidance checklist. Voice, tense, density, hedges, filler, transitions that announce, sentence-case headings, em dashes, Oxford commas, link mechanics, terminology consistency. The check is mechanical.
3. Run `reviewing-documentation` for the formal pass. Address findings before commit.

### Self-review heuristics

- Read the first paragraph alone. Does it name what the page is for? Could a reader stop there and still take away the right impression?
- Pick a random paragraph. Could the sentences swap order without losing meaning? If yes, the paragraph is carrying more than one idea or restating itself.
- Search the page for each hedge and filler word in the ban list. Each hit is a candidate for removal.
- Search for the words *will* and *would*. Most uses are tense drift — replace with present tense.
- Search for `**` (markdown bold) and `|---|` (tables). Both should return zero hits — except in worked examples that demonstrate what to remove, where one hit per demonstration is expected.

### When to defer to a structural skill

- The shape of the artifact (sections, ordering, and naming conventions) is the structural skill's territory. Skill files have a four-section shape; ADRs have context/decision/consequences; notes are atomic. This skill governs the prose inside the shape.
- When a structural skill exists for the artifact you are writing, load it alongside this one. This skill plus the structural skill together carry the contract.
- When no structural skill exists yet and the artifact is recurring, the first instance is the seed. Codify the shape in a structural skill once the pattern is clear.
