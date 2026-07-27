---
title: Walk the corpus one directory at a time
summary: "Replace the recursive listing and its exclude argument in the catalog MCP server's contents tool with a per-directory walk: the report leads with the full directory subtree and per-directory document counts, then non-markdown paths, then the documents in the requested directory alone."
tags: [todo, mcp, design]
created: 2026-07-26
priority: high
effort: medium
status: closed
cites: "[[docs/specs/hoplite-tool-api.md]]"
---

# Walk the corpus one directory at a time

Replace the recursive listing and its `exclude` argument in the `catalog` MCP server's `contents` tool with a per-directory walk. The report leads with the full directory subtree and per-directory document counts, then non-markdown paths, then the documents in the requested directory alone.

The tool lives at `plugins/hoplite-mcp/src/hoplite_catalog/`. `contents.py` holds the slicing core, `server.py` the stdio JSON-RPC host and the tool description.

## Why

`contents(under="docs")` returns 163 documents and about 16,800 tokens, past what a tool result can carry. The `keys` and `exclude` arguments cut that to 3,600, but both make the caller pay attention to size before knowing what is there.

A per-directory walk inverts it. `contents("docs")` costs about 50 tokens and answers "what is in this corpus" — seven directory names and their counts. The caller then spends tokens only on the directory it wants: glossary 1,891, journal 6,089, specs 1,519. The caller pays for the directory it asked for, not for the corpus.

Measured on the two corpora that exist today, hoplite's `docs/` and kingo's at `D:\projects\kingo\kingo\docs`:

| | documents | whole corpus | directories | max depth |
|---|---|---|---|---|
| hoplite | 163 | 16,800 tok | 7 | 1 |
| kingo | 54 | 4,736 tok | 7 | 1 |

Kingo is small enough to need no size relief at all. The orientation value is the reason that holds at any scale.

## The report

Three parts, in this order.

1. The directory subtree, every directory at every depth, names only, each with the count of documents directly in it. Names are cheap — the whole of hoplite is about 50 tokens — so the caller sees the skeleton in one call and needs no round trip per level.
2. Non-markdown files in the requested directory, path only. They cannot carry frontmatter, but hiding them makes the listing lie about what the directory holds.
3. The markdown documents in the requested directory, path and frontmatter, exactly as `contents` renders them now.

`docs/` holds no documents in either corpus, so "0 documents here" is a real answer rather than an error.

## Decisions already made

- The subtree is printed to full depth, not one level.
- Counts are direct, not cumulative: the number a caller gets by asking for that directory, which is what they are budgeting against.
- Non-markdown files are listed by path alone.
- They need their own labelled group. A bare path already means "markdown document with no frontmatter" — `docs/notes/skills-from-anthropic.md` is the one such document in this corpus — so an unlabelled PDF path would be indistinguishable from it.
- `exclude` goes away. Its purpose was skipping `docs/journal`, and a caller who does not walk into a directory has already skipped it.

## What this deletes

`exclude` takes four functions with it: `normalize_exclusions`, `resolve_exclusions`, `is_excluded`, and the whole-path-segment matching rule, plus their tests. Every review finding that clustered around exclusion spellings and validation goes with them.

## Directories recurse, documents do not

"Non-recursive" narrows to the document listing. Building the subtree walks the directory structure to full depth, but only at `stat` level; no file outside the requested directory is opened. The cost of the header is the directory count, not the document count.

## Open questions

**Does the listing respect `.gitignore`?** `docs/Graph_Databases_2e_Neo4j.pdf` is gitignored and `docs/Screenshot 2026-06-25 003628.png` is untracked. The corpus is the repo, so a gitignored file is deliberately outside it. Reporting a stray PDF is also the point of naming non-markdown files at all. Reporting everything on disk is the current answer, because a listing that hides files is the failure this tool must not produce.

**Does the subtree walk need the containment check?** A symlinked directory inside the corpus is invisible today, because `rglob("*.md")` does not recurse into one. A directory scan would list it as walkable, and asking for it would read its files and hit the containment guard in `collect`. That is an improvement: the directory becomes visible and refusable instead of silently absent. The tree walk needs the same check, or a symlinked directory pointing outside the corpus shows as walkable and fails only on the second call.

## Shape of done

- `contents` recurses for directories and not for documents.
- The report carries the subtree with counts, then non-markdown paths, then documents.
- `exclude` and its four functions are gone, along with their tests and their entries in the tool description and `plugins/hoplite-mcp/README.md`.
- `keys` still works and still defaults to every property.
- The gate is green: `ruff format --check`, `ruff check`, `pyright` strict, and the suite, all run from `plugins/hoplite-mcp/`.

## See also

- [[docs/specs/hoplite-tool-api.md]] — the tool surface this extends, and its error model.
- [[docs/todos/report-the-frontmatter-key-vocabulary.md]] — the other accepted addition to the same tool surface; independent of this one.
