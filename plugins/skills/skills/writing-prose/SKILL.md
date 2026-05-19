---
name: writing-prose
description: Use when writing, refactoring, or composing prose for markdown-based artifacts. Covers editorial guidance for rhetorical context, density, structure, and formatting.
---

# Writing prose

Foundational editorial knowledge lives here — the authoring virtues that apply across all markdown-based artifacts. Downstream skills specify the rhetorical context for the artifact under composition — writer, voice, ethos, stance, audience, subject, genre, tone, register, intent. Downstream skills may deviate with justification.

## Rhetorical context — meta-rules for downstream skills

Register emerges from the artifact's intent and audience. Downstream skills may explicitly name it; otherwise, derive it.

Downstream skills declare their full rhetorical context as a `## Rhetorical context` section in their own SKILL.md — a bulleted list with one `Slot: value` line per slot, covering all ten: writer, voice, ethos, stance, audience, subject, genre, tone, register, intent.

The Register slot is bundled shorthand: declaring a named register (catalog below) overrides only the few slots that distinguish that register from the defaults; the rest stay at default. Inheritance precedence, highest to lowest: explicit slot declaration > register bundle > the default values below. Subject and intent have no default; every downstream must declare them.

### Default rhetorical context

- Writer: contributor — someone with stake in the project, presumed knowledgeable about the subject.
- Voice: declarative, terse — direct claims without hedging.
- Ethos: expert — the writer is presumed authoritative within the subject's scope.
- Stance: neutral — describes rather than advocates, except in vision and design genres where position-taking is the point.
- Audience: another engineer — developer-facing by default; downstream may narrow to learner, operator, oncall, end user, etc.
- Subject: varies by artifact type — downstream must declare.
- Genre: reference — the most general technical-writing default; downstream may pick tutorial, how-to, explanation, vision or design, specification, ADR, note, or journal.
- Tone: professional, even-keeled — neither warm nor cold; addresses the reader as a colleague.
- Register: authoritative-declarative-terse — direct, position-taking, no hedging.
- Intent: varies by artifact type — downstream must declare.

### Deriving a register

1. Identify the artifact's intent (its purpose) and audience (who reads it). The register follows.
2. Verify against siblings — they should be consistent with the derived register. If they aren't, something is off (yours or theirs).
3. When the intent or audience is unclear, ask the user.
4. When the register cannot be determined, use the default: authoritative-declarative-terse — direct, position-taking, no hedging.

### The named registers and their tells

Each entry below is a bundled shorthand. Declaring the register name in a downstream's Rhetorical context section implies the voice, tone, audience, and approach described in the entry. Explicit slot declarations override the bundle.

- Tutorial — friendly, walks the reader through one task at a time, builds understanding in sequence, second person, present tense, imperative steps.
- How-to — task-oriented, assumes the reader knows what they want, terse imperative steps, no teaching framing.
- Reference — dry, dense, factual, organized for lookup rather than reading, declarative, third person where appropriate, exhaustive on the surface area it covers.
- Explanation — understanding-oriented, conceptual, expository, often comparative or historical, longer-form prose.
- Vision or design — authoritative, declarative, position-taking, terse, explicit about what is open versus settled.
- Specification — normative, contractual, RFC-style with MUST/SHOULD/MAY, exhaustive on requirements.
- ADR — declarative, present-tense, describes the current state of a system, mutable but always current, replaces prior content as the state changes.
- Note — rough, exploratory, no audience commitment, ephemeral scratch that may be rewritten or deleted freely.
- Journal — observation-based, internal-facing, chronological, dated, append-only, immutable once written, first-person acceptable, records discoveries and issues at a point in time.

## Composition — authoring virtues and how to apply them

Above all: prefer positively framed assertions. Say what is, not what it isn't. Positive constructions strengthen the message. Negative constructions weaken it. Weak writing circles around what something isn't. It gestures rather than delivers.

See [positive-transforms.md](${CLAUDE_PLUGIN_ROOT}/skills/writing-prose/reference/positive-transforms.md) for examples of negative to positive transformations when you need help forming a positive frame.

Each principle bullet has an expansion file at `${CLAUDE_PLUGIN_ROOT}/skills/writing-prose/reference/<slug>.md`, where the slug is the principle phrase lowercased with non-alphanumerics replaced by dashes (use `bash ${CLAUDE_PLUGIN_ROOT}/scripts/slugify.sh '<principle phrase>'` to derive deterministically). Consult when depth, examples, or patterns are needed. For example, in "- Source is the authority — defer to the subject;", "Source is the authority" is the phrase.

- Source is the authority — defer to the subject; verify against it before claiming; cite by stable reference.
- Active voice over passive — agency stays with the actor; "the user signs in," not "sign-in is performed by the user."
- Present tense for current behavior — "the function returns," not "the function will return" or "the function returned."
- Second person for instructions — address the reader directly with "you"; avoid "the user" or "one."
- Systems behave — describe what they do; "wants" and "decides" belong to people.
- Every word must earn its place — cut hedges, filler, transitions that announce; clarity outranks brevity at the cut-line.
- Verbs over nominalizations — "decide" beats "make a decision"; the verb is shorter and stronger.
- Strong verbs over verb-plus-adverb — "sprint" beats "run quickly"; the verb carries the meaning.
- Concrete over abstract — "the cache" beats "the caching mechanism" unless the distinction is the point.
- Substance over superlatives — the reader judges, not the writer; avoid hollow words like "seamless," "robust," "powerful."
- Assertions over commentary — let each statement stand; skip motivational framing and stage-setting like "let's dive into" or "great writing requires care."
- English over Latin — "for example" beats "e.g."; "that is" beats "i.e."; "and so on" beats "etc."
- Global English — avoid regional idioms, cultural references, sports metaphors; many readers aren't native speakers.
- One idea per sentence — every sentence carries one claim; complex sentences split into simple ones.
- State each idea once — every fact has one home; link to it rather than restating it; no paragraph restates an adjacent paragraph.
- Parallel construction in series — items in a list share grammatical shape; one verb form, one sentence pattern.
- Expository ordering — main idea before mechanics; conclusions before justifications.
- Cohesion within a document — each paragraph picks up where the previous left off; topic threads run through.
- Anticipate the reader's question — write what they need to know next, not what's next in the writer's head.
- Front-load important words — the most informative word goes first in the sentence and first in the bullet.
- Self-contained artifacts — each page stands on its own; link to canonical definitions rather than restate, or define on first use.
- Cohesion across documents — siblings share register, terminology, and pattern; the corpus is a connected whole.
- Action-oriented headings — "Configure the database" beats "Database configuration"; the heading names what the section does.
- Examples carry weight — one brief example per rule, only when the rule isn't self-evident; before-and-after when the rule transforms shape.
- Forms are the schema — every recurring artifact has a canonical shape; the shape is the contract; the prose fills it.
- The first page sets the pattern — the first instance teaches the next ten; invest disproportionate care.
- Name pattern deviations — when departing from an established pattern, name the deviation and explain why; undocumented deviation teaches the next author to copy the wrong pattern.
- Markdown is the wire format — human-readable in source, LLM-readable without a renderer, diffable in git; no HTML, no bespoke markup.
- Terminology hygiene — capitalize defined role names; domain terms used across pages belong in a glossary; expand acronyms on first use; name the context when meaning differs.

## Grammar, structure, and referential integrity

- Em-dash usage — `—` for parenthetical breaks, definitions, and appositives; not double hyphens.
- Oxford comma — `nodes, edges, and memos` for lists of three or more.
- Backticks — for code, paths, identifiers, and CLI commands; fenced code blocks with language tags for multi-line samples.
- Link form — `[text](path)`; the link text names the target, never `click here` or `this page`.
- Sentence-style headings — first word and proper nouns only; no title case.
- Numbered for procedures, bullets for options, prose for reasoning.
- Skip bold and tables — except in worked examples that demonstrate what to remove.
- Rename propagation — on renames and refactors, grep the project for the old name or path before declaring done; update every reference in the same change set.

## Validation — self-check the composition before handoff

### Self-review — mechanical checks

Run `reviewing-prose` for the formal pass; address findings before commit.

### Self-review — apply judgement 

- Lede check — read the first paragraph alone; does it name what the artifact is for? Could a reader stop there and still take away the right impression?
- Within-document cohesion read — read paragraph transitions; does each pick up from the previous, or do paragraphs sit as independent claims?
- Cross-document cohesion read — compare against sibling artifacts; do register, terminology, and structural pattern hold across them?
- Link-strip test — read the page imagining every link is broken; does the core message still come through? If not, more context is needed inline.
- Negation grep — `not`, `don't`, `didn't`, `wasn't`, `won't`, `can't`, `cannot`, `never`, `avoid`, `should not`, `didn't seem`, `wasn't very`. Each hit is a candidate for positive rewrite; see [positive-transforms.md](${CLAUDE_PLUGIN_ROOT}/skills/writing-prose/reference/positive-transforms.md).
- Hedge and filler grep — `might`, `perhaps`, `could be`, `it's worth noting`, `basically`, `simply`, `just`, `actually`, `really`, `quite`, `very`. Each hit is a candidate for removal.
- Tense drift grep — `will`, `would`. Most uses are tense drift; replace with present tense.
- Marketing language grep — `seamless`, `robust`, `powerful`, `revolutionary`, `easy`, `simple`, `intuitive`. Cut or replace with substance.
- Latin abbreviation grep — `e.g.`, `i.e.`, `etc.`. Replace with English equivalents.
- Bold and table grep — `**`, `|---|`. Both return zero hits except in worked examples that demonstrate what to remove.
- Source verification — for any claim about behavior, verify against the actual source (code, schema, document); update one if they disagree.
