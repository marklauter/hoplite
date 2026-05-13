# Write the writing-skills and reviewing-skills pair

Tags: todo,skills
LLM-targeted structural pair layered on the writing-documentation editorial spine; lands now that the documentation pair has settled.


## Observation

The `writing-documentation` / `reviewing-documentation` pair settled across commits `e9cda8c` through `ea53d33`. During design we agreed that skills, agent prompts, and slash commands form a distinct genre — LLM-targeted prose with extreme density requirements, the canonical four-section shape, and no bold/tables — and that the dedicated pair lands after the documentation pair stabilizes. The documentation pair has now stabilized.

## Interpretation

`writing-skills` loads `writing-documentation` as the editorial spine and layers the structural conventions for skill files on top:

- The canonical four-section shape (intro → Philosophy → Guidance → Validation).
- Named-anchor Philosophy intro with one paragraph of orienting threads, then `###` headings.
- 1:1 Philosophy/Guidance mirror as the default; document any deviation explicitly.
- Frontmatter contract: `name`, `description` only; description carries the trigger language.
- The skill body intro: describes file content only; never narrates loading or repeats the trigger.

`reviewing-skills` mirrors with lens additions on top of `reviewing-documentation`:

- A structural lens (canonical four sections present, Philosophy/Guidance mirroring, frontmatter shape).
- A trigger-language lens (description verbs match the skill's actual scope).
- Reuses the shared `scripts/` infrastructure under the existing `Type: <code|documentation|skill?>` taxonomy — likely add a third `Type:` value (`skill`) and a corresponding rubric in `summarize.sh`.

Both pairs operate on `.md` files under `**/skills/<name>/SKILL.md`. The Per-lens signals borrow heavily from `reviewing-documentation` but tighten the bar — bold and tables in a skill are always violations; in a doc they have documented worked-example exceptions.

## Next

- Confirm scope: does `writing-skills` cover only Anthropic-style Claude Code skills, or also agent system prompts and slash commands?
- Decide whether the `Type:` taxonomy in `report-finding.sh` and friends grows a third value (`skill`) now, or whether skill findings reuse `Type: documentation` with an additional dimension.
- Draft `writing-skills` first; `reviewing-skills` is the easier follow-on once the rubric is fixed.
