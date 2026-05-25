# Skill composition

Tags: meta,skills,composition,architecture,injection,components
How SKILL.md files share content across skills. Two mechanisms coexist: load-composition (downstream loads foundation, inherits via prose contract) and component injection (consumer cat-injects shared fragments at load time). Injection is the newer mechanism that turns "shared content" from a load-order convention into a literal architecture.

## Motivation

Prose-artifact skills (`writing-prose`, `writing-wiki`, `taking-notes`, `journaling`, plus the reviewing-* counterparts) overlap on universals — positive framing, dedup discipline, link discipline — while diverging on specifics like audience, tone, register, voice, intent. Restating universals in every skill courts drift: when one skill's positive-framing rule moves and the others remain, the corpus splits into incompatible interpretations of the same idea.

Paired `writing-*` / `reviewing-*` skills carry the same risk between authoring and review. If `writing-wiki` and `reviewing-wiki` each restate philosophy independently, the rubric reviewing against can drift from the rubric writing to.

Composition addresses both: one canonical statement of the universals, all consumers pull from it.

## Architecture: foundation and downstream

The first organization was load-composition. One skill is the foundation; downstream skills load it first, then declare what they override. Coupling is one-way: the foundation knows nothing about its downstreams; exceptions live in the skill that needs them.

- `writing-prose` is the foundation. It states the general laws of good writing and declares that audience, tone, register, voice, and intent MUST be set by the downstream.
- Downstream skills (`taking-notes`, `journaling`, `writing-wiki`, etc.) load the foundation first, fill the rhetorical-context slots for their artifact, and explicitly override or soften foundation rules where the use case demands it (e.g., journaling softens positive framing for private emotional honesty).
- Paired `writing-*` / `reviewing-*` skills both inherit from the same foundation so philosophy stays aligned between authoring and review.

Tentative: whether foundation rules should be named and enumerable with RFC-style MUST / SHOULD / MAY markers so a downstream can cite the specific rule it is overriding. The marker discipline has yet to be adopted.

## Mechanism: injection at load time

Load-composition is a prose contract — the downstream tells the agent to load the foundation, and the agent does it. Injection makes the composition literal. A SKILL.md can include a backtick-bash directive that the loader executes, replacing the directive with the command's stdout.

```markdown
!`cat ${CLAUDE_PLUGIN_ROOT}/components/<name>/<name>.md`
```

Plain `cat` is the default for plain-markdown fragments authored without YAML frontmatter — they inject cleanly. The directive line is gone from the loaded content; the fragment's body sits in its place.

Verified 2026-05-20 in two phases inside the `skills` plugin:

1. **Frontmatter-bearing target (awk strip)** — injected `writing-prose/SKILL.md` into `taking-notes/SKILL.md` with awk to remove the YAML frontmatter; reloaded and observed the inlined content land where the directive was.
2. **Plain-markdown fragment (cat)** — created a fragment with a unique marker, injected via `!`cat into the same SKILL.md, reloaded, and confirmed the marker appeared mid-skill.

### Awk when frontmatter is in the way

To inject a file that carries a YAML frontmatter block (one SKILL.md inlining another, for example), strip the frontmatter with awk:

```markdown
!`awk 'NR==1 && /^---$/ {in_fm=1; next} in_fm && /^---$/ {in_fm=0; next} !in_fm' ${CLAUDE_PLUGIN_ROOT}/skills/<skill>/SKILL.md`
```

The awk command strips a `---`-delimited block only when one starts at line 1; files without frontmatter pass through untouched. Cleaner authoring practice: write shared content as plain-markdown fragments without frontmatter so plain cat suffices.

### Fragments are live-read on every reload

Edits to an injected fragment propagate via `/reload-plugins` without touching the consumer SKILL.md. The loader runs the bash command fresh on each load; fragments are read at injection time, not baked in at install time.

Implication: a single shared fragment under `plugins/armory/components/<name>/` is the source of truth for cross-cutting content. Editing it updates every consuming skill on the next reload; consumer SKILL.md files stay untouched.

### The nested env-var limitation

The loader expands `${CLAUDE_PLUGIN_ROOT}` once, against the outer SKILL.md source. The `!`-injected stdout arrives as opaque bytes and ships through to the agent verbatim; the loader does not re-walk the injected content to expand variables a second time.

Concrete effect: any `${CLAUDE_PLUGIN_ROOT}` references inside a fragment's body text reach the agent as literal placeholders. Confirmed with both cat and awk — the limitation is in the loader, not the choice of injection command.

### Resolving `${CLAUDE_PLUGIN_ROOT}` inside the injected body

Pipe the cat output through `sed` using a character-class regex to protect the `$` from the loader's pre-expansion. Validated 2026-05-21:

```markdown
!`cat ${CLAUDE_PLUGIN_ROOT}/components/<name>/<name>.md | sed "s|[$]{CLAUDE_PLUGIN_ROOT}|${CLAUDE_PLUGIN_ROOT}|g"`
```

Why the character class: the loader pre-expands `${CLAUDE_PLUGIN_ROOT}` in the directive before invoking the shell, and strips backslash escapes during the pass. A `\${CLAUDE_PLUGIN_ROOT}` escape on the LHS fails — the loader expands both sides to the same absolute path, leaving sed with a no-op. `[$]` is a regex character class the loader leaves alone; it reaches sed as the literal pattern `${CLAUDE_PLUGIN_ROOT}`. The RHS bare `${CLAUDE_PLUGIN_ROOT}` expands at load time to the absolute path — exactly what gets substituted in.

`|` is the sed delimiter to skip slash-escaping the absolute path.

Fallback — `envsubst` (gettext; ships with Git Bash on Windows, default on Linux/macOS):

```markdown
!`cat ${CLAUDE_PLUGIN_ROOT}/components/<name>/<name>.md | envsubst`
```

Cleaner syntax. Caveat: expands every env var referenced in the fragment body, not only `CLAUDE_PLUGIN_ROOT`. If a fragment ever quotes `$HOME` or `$PATH` as example text, envsubst substitutes. The sed pattern is surgical and safer for editorial fragments.

## Knowledge, not command

Skills are content dumps, not action triggers. The metaphor: jacking knowledge into the agent's head, the way Neo learns kung fu — having the knowledge is a separate activity from being told to fight. A skill teaches the agent about a topic; the agent decides when to apply it.

This shapes the SKILL.md spine: lead with the editorial content (what the artifact is, how it reads well), demote trigger phrases to a short "when this skill applies" section. The spine is the knowledge; triggers serve the agent's decision of whether the user's request fits.

## SKILL.md authoring conventions

Three rhetorical conventions govern how a SKILL.md presents itself.

### H1 summary is didactic meta-discourse

The summary line directly under the H1 is didactic meta-discourse: it teaches the reader the interpretive frame for the rest of the document before any subject content arrives. It does not merely position the skill — it installs the lens through which every following section is read. By the end of the summary, the reader knows what the skill is, how to treat the rules below (as inheritable defaults, as overridable patterns, as a foundation expecting a downstream), and which other skills compose with it.

Worked example — the v1 `writing-prose/SKILL.md` intro: "Foundational editorial knowledge lives here — the authoring virtues that apply across all markdown-based artifacts. Downstream skills specify the rhetorical context for the artifact under composition — writer, voice, ethos, stance, audience, subject, genre, tone, register, intent. Downstream skills may deviate with justification." Three sentences install three primes: treat what follows as a foundation rather than a complete picture; expect a second layer to fill in rhetorical context; read every rule as overridable given justification. Without those primes, the same content would parse as monolithic rules.

The v2 thin-shell `writing-prose/SKILL.md` carries a single-sentence intro because its body is now the injected fragment, which carries its own intro. The principle holds at both levels.

### Soft on procedure

A skill is content, not a recipe. Offer principles that let the agent exercise judgment, not strict step-by-step workflows. The reader is an agent with context the skill author can't anticipate; rigid procedures break against cases the author never imagined, while principles travel.

### Direct instruction

A skill teaches the agent about a topic or task. It is an instructional block — direct in its assertions, not allusive. Say what something is and how to do it: "this is how you preserve durable ideas — write a note." "This is how you compose a note." Indirection and meta-framing dilute the teaching; direct prose carries it. Pairs with [Soft on procedure](#soft-on-procedure) — that one governs the form (principles over rigid workflows); this one governs the voice (direct over allusive).

## The realized shape — composition from component instruction sets

The injection mechanism fits the "always load this companion content" pattern — inline-not-sidecar in mechanical form. Plain-markdown fragments under `plugins/armory/components/<name>/` are the canonical home for cross-cutting content; consumer skills inject what they need via `!`cat`. Composite skills become a thin spine plus a handful of injected fragments — skill composition from component instruction sets.

Under injection, prose that taught load-composition becomes overhead. Phrases like "downstream skills declare their full rhetorical context..." or "default values the downstream falls back to..." earn their place when the downstream is a separate file referencing defaults; once the same content is inlined at load time, there is no inheritance to teach. The substantive editorial content — principle bullets, grammar rules, validation greps — is universal and belongs verbatim in every consumer. When extracting a foundation into a component, trim the scaffolding prose and keep the substance.

The foundation skill itself becomes a thin shell: frontmatter for discoverability plus the `!`cat` directive against its own component fragment. Direct invocation (e.g. `/writing-prose`) still works while the content lives once under `components/`.

Expansion files referenced by a fragment (a `reference/` subdirectory, for instance) live alongside the fragment in the same component directory. This sidesteps the nested env-var limitation for path references — paths reachable from `${CLAUDE_PLUGIN_ROOT}/components/<name>/` resolve correctly whether the consumer is the foundation skill itself or any downstream.

(see migration-pattern-for-refactoring-writing-skills.md for the operational recipe used to move legacy skills into this shape.)

## Reproducing the experiment

Setup: a Claude Code plugin with at least one consumer skill and a place to put a shared fragment.

1. Create a plain-markdown fragment at `plugins/<plugin>/components/test-cat-injection.md`. Content: a short H2 heading plus a unique marker string. No YAML frontmatter.

2. Open the consumer skill's SKILL.md. Pick a line near the top and replace it with the directive:

   ```markdown
   !`cat ${CLAUDE_PLUGIN_ROOT}/components/test-cat-injection.md`
   ```

3. Run `/reload-plugins` in the Claude Code session.

4. Invoke the consumer skill — `/skills:<skill>` or any matching trigger.

5. Inspect the loaded skill content as the agent receives it. Three observations confirm the mechanism:

   - The `!`-backtick line is gone; the fragment's body appears in its place.
   - The unique marker from the fragment is present mid-skill.
   - The outer skill's own `${CLAUDE_PLUGIN_ROOT}` references appear as resolved absolute paths.

6. Test live-read: edit the fragment (add a recognizable string), run `/reload-plugins`, invoke the skill again. The edit appears in the loaded content without re-touching the consumer SKILL.md.

7. Test nested env-var behavior: include a literal `${CLAUDE_PLUGIN_ROOT}/...` string in the fragment's body text. The reference arrives literal — outer substitution happens, substitution inside `!`-injected stdout does not.

Teardown: revert the SKILL.md change and delete the test fragment.

Variant for the sed workaround: replace the `!`-injection in step 2 with the piped sed form above, then repeat steps 3-7 to confirm the workaround resolves the nested references.
