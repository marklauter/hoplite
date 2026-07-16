---
title: Add a negation-grep self-review check to writing-prose Validation
summary: A mechanical self-review pass that greps draft prose for negation trigger words and prompts a rewrite-as-positive pass; operationalizes the golden rule of positive framing.
tags: [todo, skills, writing-prose, validation]
created: 2026-05-25
aliases: []
---

## Observation

writing-prose's golden rule is positive framing — "say what is, not what it ain't." LLMs default to negative-framed prose because their training corpus (security writing, legal, regulatory, instruction manuals, most documentation) is dense with `not`, `don't`, `never`, `avoid`, `cannot`, `won't`. Stating the rule prominently at the top of the Composition section is what the foundation can do; enforcement has to happen at review time.

The article at https://armlinhouse.com/say-what-it-is-not-what-it-isnt/ argues the mechanism: negative constructions force a cognitive detour — the reader has to construct the positive then mentally negate it. The author's example: "didn't excite Cinderella" vs "filled Cinderella with dread" — the rewrite delivers emotion directly. Closing line: "Strong writing tells the reader what something *is*. Weak writing circles around what it *isn't*."

## Interpretation

A mechanical self-review check in writing-prose's Validation section operationalizes the golden rule. The check has two parts:

- **Grep list:** `not`, `don't`, `never`, `didn't`, `wasn't`, `won't`, `can't`, `cannot`, `avoid`, `should not`, plus phrase patterns `didn't seem`, `wasn't very`. Each hit is a candidate, not an automatic defect — Define-by-presence permits natural negations.
- **Rewrite prompt:** when a hit appears, ask "What is this sentence actually trying to say?" and rewrite directly. Most hits collapse into a tighter positive assertion.

This pattern matches existing Validation heuristics in the original SKILL.md ("Search for the words *will* and *would*. Most uses are tense drift — replace with present tense.") — same mechanical grep + judgment-based reframe shape.

## Next

- Land the Validation section of writing-prose (task #5 covers this) with the negation-grep heuristic as one of its bullets.
- Consider also adding a transform-pattern catalog (negative → positive rewrite examples) so the LLM has concrete patterns to match against: `Don't bury the lede` → `Front-load the lede.` etc.
- Once Validation lands, propagate the same heuristic into reviewing-prose (the paired reviewer skill, post task #6) so findings can cite the negation as a violation of the golden rule.

## Other desired features for the same script

The negation-grep is the seed for a broader mechanical self-review script under writing-prose's Validation section. Additional checks the script should cover, all of the same shape (grep for trigger pattern, report candidates, judgment applies to fix):

- **Em-dash discipline** — flag single dashes (` - `, hyphen with spaces) used where em-dashes are required for parenthetical breaks, definitions, and appositives. Replace with ` — `. Edge case: compound modifiers like `verb-plus-adverb` use hyphens correctly and must not false-positive.
- **Hedge and filler grep** — `might`, `perhaps`, `could be`, `it's worth noting`, `basically`, `simply`, `just`, `actually`, `really`, `quite`, `very`.
- **Tense drift grep** — `will`, `would`. Most uses are tense drift; replace with present tense.
- **Marketing language grep** — `seamless`, `robust`, `powerful`, `revolutionary`, `easy`, `simple`, `intuitive`.
- **Latin abbreviation grep** — `e.g.`, `i.e.`, `etc.` — replace with English equivalents.
- **Bold and table grep** — `**`, `|---|` — both expected to return zero hits except in worked examples that demonstrate what to remove.

The script reports candidates per check; the user (or downstream agent) applies judgment to each hit, since natural-negation and demonstration-example exceptions exist for several patterns.
