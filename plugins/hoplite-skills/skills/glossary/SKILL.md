---
name: glossary
description: Reduce a resolved term to its kernel — a word plus the smallest phrase that unpacks it — and write it to the glossary. Use when a term settles, or when a definition needs collapsing, reducing, or locking.
---

# Glossary

A definition is a statement that fixes a term's meaning by naming the nearest class to which the term belongs and the property that distinguishes it within that class. It is a single statement that contains the genus and its differentiae and nothing else. Keep cutting until the next cut would take the genus or a differentia. What's left after the cuts is the kernel.

A glossary entry carries one term's kernel. Reduce before you write, and lock only when the kernel is reduced and resolved.

- A summary opens on the class the term belongs to, then narrows. A noun takes an indefinite article and its genus: *an evaluation that applies…*, *a set of facts closed under…*. A verb takes the infinitive: *to decide whether…*. The differentia that follows cuts the class down to the term.
- Several words for one idea are one term. Keep the canonical word and retire the rest into `retired`. A retired word that had its own glossary file also goes in `aliases`, so existing links still resolve. "`couch`, `settee`, and `davenport` name one thing, so they retire into `sofa`."
- A definition carries meaning, not mechanism. Implementation belongs to the term it describes, so move it there. "`engine` is *a machine that converts fuel to motion*, not *the spark-plug firing order* — that belongs to `ignition`."
- An overloaded word is an incomplete reduction, not a kernel. Each sense in the domain has its own precise word, so find both words and retire the overloaded one into them. A second file never appears under the same name. "`bug` did double duty: the creature sense reduced to `insect`, the fault sense to `defect`, and `bug` retired into them — because `bug.md` existed, it aliases `defect` too."
- A term locks when it is reduced and resolved. The next cut would cost meaning, and the word carries one sense with its contrasts drawn; that entry takes `status: locked`. Until both hold it stays `evolving`.

Write to the [Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide/welcome/) — plain and scannable; say what a thing is before how to use it.

Write `docs/glossary/<term>.md` (kebab-case) to the frontmatter standard (`${CLAUDE_PLUGIN_ROOT}/references/frontmatter.md`):

```markdown
---
title: <term>
summary: "<the smallest phrase that unpacks it>"
tags: [glossary, <grouping>]
aliases: [<retired page name>, ...]
created: YYYY-MM-DD
status: <evolving | locked>
retired: [<retired term>, ...]
is-a: "[[<broader-term>]]"
contrast:
  - "[[<other-term>]]"
  - "[[<another-term>]]"
---

<the summary, verbatim>

## Examples

- <a concrete instance — the term in use, not more definition>

## Contrasts

- `<contrast-term>` — <one line drawing the boundary against it — never implementation detail>
```

- `aliases`, `retired`, and the edge keys are optional; omit when empty.
- An edge is a property whose value is a quoted wikilink — the key names the relationship, the value the target, like `is-a: "[[...]]"`; there is no `edges:` list and no `edge.` prefix (edge/link syntax: `${CLAUDE_PLUGIN_ROOT}/references/expressing-edges.md`).
- Index it — add `- [[<term>]]` to the `## Terms` list in `docs/glossary/README.md`, kept alphabetical.
- Examples — the optional `## Examples` section illustrates the term with concrete instances; the definition stays in the summary, and an example never restates it. Omit the section when there are none.

## Edge keys

The frontmatter key names the relationship the edge expresses, read `<source> <key> <target>`. The vocabulary is open, but reach for a recognized relation below before coining a new one. Edge direction follows dependency; only symmetric edges reciprocate.

- Directional — the default. The edge lives on the dependent's side and points at what it depends on; the target stays ignorant, so a new dependent never edits it.
  - `is-a:` — species → genus. Transitive.
  - `has-a:` — whole → part.
- Symmetric — reciprocated. The relationship reads identical from both ends, so write it on both terms: add this term back on the target and give it a `## Contrasts` bullet, one per target.
  - `contrast:` — opposite; a mutual boundary.

## Proofread

The artifact is not done until it has been proofread. Before presenting it, committing it, or ending the turn, invoke the `proofreading` skill (`hoplite-skills:proofreading` via the Skill tool) and follow its instructions on the artifact.
