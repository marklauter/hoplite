# SKILL.md supports backtick-bash injection at load time

tags: discovery,skills,claude-code,env-vars
SKILL.md executes backtick-bash injection lines at load time and inlines stdout; ${CLAUDE_PLUGIN_ROOT} resolves in the outer file but stays literal inside the injected content, and fragments are re-read on every /reload-plugins.

## Confirmed mechanism

A line of the form `` !`<bash command>` `` inside a SKILL.md executes when the plugin loader reads the file. The command's stdout replaces the backtick block in the loaded content the agent receives.

Verified 2026-05-20 in two phases inside this plugin:

1. **Frontmatter-bearing target (awk strip)** — injected `writing-prose/SKILL.md` into `taking-notes/SKILL.md` with awk to remove the YAML frontmatter; reloaded and observed the inlined content land where the directive was.
2. **Plain-markdown fragment (cat)** — created `plugins/skills/shared/test-cat-injection.md` (no frontmatter, contained a unique marker), injected via `!`cat into the same SKILL.md, reloaded, and confirmed the marker appeared mid-skill.

## The canonical sample

```markdown
!`cat ${CLAUDE_PLUGIN_ROOT}/components/<name>/<name>.md`
```

Plain `cat` is the default for plain-markdown fragments — fragments authored with no YAML frontmatter inject cleanly. The directive line is gone from the loaded content; the fragment's body appears in its place.

## When awk (or any preprocessor) is needed

Only when the injected file carries a YAML frontmatter block that should be stripped. For full SKILL.md injection (e.g., one skill inlining another), use awk:

```markdown
!`awk 'NR==1 && /^---$/ {in_fm=1; next} in_fm && /^---$/ {in_fm=0; next} !in_fm' ${CLAUDE_PLUGIN_ROOT}/skills/<skill>/SKILL.md`
```

The awk command strips a `---`-delimited block only when one starts at line 1; files without frontmatter pass through untouched. Portable POSIX awk.

Cleaner authoring practice: write shared content as plain-markdown fragments without frontmatter, so plain cat suffices.

## Fragments are live-read on every reload

Edits to an injected fragment propagate via `/reload-plugins` without touching the consumer SKILL.md. The loader runs the bash command fresh on each load; fragments are not baked in at install time. Confirmed when a fragment edit appeared in the loaded consumer skill content immediately after the next reload.

Implication: a single shared fragment under `plugins/skills/shared/` is the source of truth for cross-cutting content. Editing it updates every consuming skill on reload; consumer SKILL.md files stay untouched.

## The nested env-var limitation

The loader expands `${CLAUDE_PLUGIN_ROOT}` once, against the outer SKILL.md source. The `!`-injected stdout arrives as opaque bytes and ships through to the agent verbatim; the loader does not re-walk the injected content to expand variables a second time.

Concrete effect: any `${CLAUDE_PLUGIN_ROOT}` references inside a fragment's body text reach the agent as literal placeholders. Confirmed with both cat and awk — the limitation is in the loader, not the choice of injection command.

## Resolving `${CLAUDE_PLUGIN_ROOT}` inside the injected body

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

## When this matters

The injection mechanism fits the "always load this companion content" pattern — inline-not-sidecar in mechanical form. Plain-markdown fragments under `plugins/skills/components/<name>/` become the canonical home for cross-cutting content; consumer skills inject what they need via `!`cat. Composite skills become a thin spine plus a handful of injected fragments — skill composition from component instruction sets.

Under injection, prose that taught load-composition becomes overhead. Phrases like "downstream skills declare their full rhetorical context..." or "default values the downstream falls back to..." earn their place when the downstream is a separate file referencing defaults; once the same content is inlined at load time, there is no inheritance to teach. The substantive editorial content — principle bullets, grammar rules, validation greps — is universal and belongs verbatim in every consumer. When extracting a foundation into a component, trim the scaffolding prose and keep the substance.

The foundation skill itself becomes a thin shell: frontmatter for discoverability plus the `!`cat` directive against its own component fragment. Direct invocation (e.g. `/writing-prose`) still works while the content lives once under `components/`.

Expansion files referenced by a fragment (a `reference/` subdirectory, for instance) live alongside the fragment in the same component directory. This sidesteps the nested env-var limitation for path references — paths reachable from `${CLAUDE_PLUGIN_ROOT}/components/<name>/` resolve correctly whether the consumer is the foundation skill itself or any downstream.

(see skill-composition.md for the broader SKILL.md composition contract.)

## Reproducing the experiment

Setup: a Claude Code plugin with at least one consumer skill and a place to put a shared fragment.

1. Create a plain-markdown fragment at `plugins/<plugin>/shared/test-cat-injection.md`. Content: a short H2 heading plus a unique marker string. No YAML frontmatter.

2. Open the consumer skill's SKILL.md. Pick a line near the top and replace it with the directive:

   ```markdown
   !`cat ${CLAUDE_PLUGIN_ROOT}/shared/test-cat-injection.md`
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

Variant for the workarounds: replace the `!`-injection in step 2 with one of the piped forms from the Workarounds section above, then repeat steps 3-7 to confirm whether the substituted variant resolves the nested references.
