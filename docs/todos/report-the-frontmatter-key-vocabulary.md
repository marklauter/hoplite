---
title: Report the frontmatter key vocabulary
summary: "Add a second tool to the catalog MCP server returning every distinct frontmatter key in a corpus with the count of documents carrying it and whether its values are edges or claims, so the open vocabulary is inspectable and its drift visible."
tags: [todo, mcp, design]
created: 2026-07-26
priority: medium
effort: low
status: open
cites:
  - "[[docs/specs/frontmatter.md]]"
  - "[[docs/todos/predicates-are-an-open-vocabulary.md]]"
---

# Report the frontmatter key vocabulary

Add a second tool to the `catalog` MCP server returning every distinct frontmatter key in a corpus, with the count of documents carrying it and whether its values are edges or claims. In SQL over an imaginary frontmatter table it is `select key, count(*) from frontmatter group by key`.

## Why

Two reasons. The second matters more.

`contents(keys=[...])` cannot be used well without it. A caller has to guess key names, and a guess that misses returns nothing useful. The misspelled-key refusal in `_call_contents` exists only because nothing could answer "which keys exist."

The vocabulary is open by design, which means drift is invisible. Measured across the two corpora:

| | documents | keys | edge keys | keys used once |
|---|---|---|---|---|
| hoplite | 163 | 15 | 7 | 3 |
| kingo | 54 | 14 | 6 | 2 |

Ten keys are shared. Five appear only in hoplite (`retired`, `contrast`, `estimates`, `requires`, `refines`), four only in kingo (`type`, `cites`, `supports`, `scoped-by`). `aliases` is one of the four special keys and is used in neither. `created` is on 162 of 163 hoplite documents and 36 of 54 kingo ones. None of that is knowable today without a script.

The report is small — 15 keys is about 100 tokens — so it costs nothing to consult.

## The report

Per key: the key, the number of documents carrying it, and its kind.

Kind is one of three. **Claim** when no value is a wikilink, **edge** when every value is, **mixed** when both occur in different documents. Mixed fires nowhere in either corpus today. It is still worth reporting: a key that is an edge in one document and a claim in another means someone wrote a predicate name for a claim, or dropped the quotes around a link.

## Two requirements, both proven by counterexample

**Values span lines, so detection must follow continuation lines.** [[docs/specs/frontmatter.md]] allows a block list, which puts the value on the indented lines below the key:

```yaml
cites:
  - "[[identifiers]]"
  - "[[facts]]"
```

A scanner reading only the `key:` line sees an empty value. All five uses of `cites` in kingo take this form, and a first pass at this report filed them as claims for exactly that reason. `has-a` appears as both a scalar and a block list in both corpora, so per-key arity is not fixed either. The rule: a line that is indented, or starts with `- `, belongs to the last unindented `key:` above it.

`project` in `plugins/hoplite-mcp/src/hoplite_catalog/contents.py` already groups continuation lines for the `keys` argument. This report reuses that grouping rather than adding a second scanner.

**The four special keys are excluded from edge detection.** `frontmatter.md` states that a special key is read by its defined meaning, so a wikilink in one is not an edge. This is not hypothetical: one kingo journal entry has two wikilinks inside its `summary` prose, and a bare test for `[[` promotes `summary` to an edge predicate.

## Naming

`keys` collides with the `contents` argument of the same name. `vocabulary` is the corpus's own word — `frontmatter.md` calls the keys "a flat, open vocabulary" — and does not collide with `properties`, which the JSON input schema already uses.

## Not in scope

Searching for a key with a given value, the equivalent of `where status = 'locked'`, is a third tool and deliberately deferred. It depends on this one: filtering on `status` is not possible until the caller knows `status` exists.

## Shape of done

- A second tool reports key, document count, and kind over a directory of the corpus.
- Detection follows continuation lines and skips the four special keys, both covered by tests built from the counterexamples above.
- Mixed is reported when it occurs, and a test constructs the case since no corpus supplies one.
- The gate is green: `ruff format --check`, `ruff check`, `pyright` strict, and the suite, all run from `plugins/hoplite-mcp/`.

## See also

- [[docs/specs/frontmatter.md]] — the standard that defines the special keys and the value rule that separates an edge from a claim.
- [[docs/todos/predicates-are-an-open-vocabulary.md]] — why the vocabulary is open, which is what makes a report over it worth having.
- [[docs/todos/walk-the-corpus-one-directory-at-a-time.md]] — the other accepted addition to the same tool surface; independent of this one.
