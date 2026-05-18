# Add a negation-grep self-review check to writing-prose Validation

Tags: todo,skills,writing-prose,validation
A mechanical self-review pass that greps draft prose for negation trigger words and prompts a rewrite-as-positive pass; operationalizes the golden rule of positive framing.

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
