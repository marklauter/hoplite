# hoplite-mcp

The `catalog` MCP server. One tool today: `contents`.

## contents

`contents` lists every markdown document under a folder of the corpus, each with its
frontmatter exactly as written.

```
contents(under="docs/glossary")

docs/glossary/edge.md
title: Edge
summary: "A relationship between two documents."
tags: [glossary, hoplite]
status: locked
is-a: "[[relationship]]"

docs/glossary/README.md
```

The output is a path per document, followed by its frontmatter properties, one per line,
with a blank line between documents. A document with no frontmatter is a single line.

There are no `---` fences. They delimit a block for a parser reading a file, and nothing
reads this but an agent, for which the path line and the blank line already mark every
boundary. Blank lines inside a block are dropped, so a stray one cannot split a document
into two records.

`under` is a folder relative to the corpus root, and defaults to `docs`. The listing
recurses, and is ordered by path so two calls over an unchanged corpus return identical
text.

### Sizing the listing

Listing the whole corpus costs around 16,800 tokens, and `summary` is 57% of that. Since
`summary` is what makes a listing worth reading, it stays in by default, and two optional
arguments cut the cost when a folder is too large to read whole.

`keys` picks which properties to emit. `exclude` drops folders, matched on whole path
segments, before the files are read.

| call over `docs/` | documents | ~tokens |
|---|---|---|
| `contents()` | 163 | 16,800 |
| `exclude: ["docs/journal"]` | 113 | 10,700 |
| `keys: ["title", "tags", "status"]` | 163 | 5,800 |
| both of the above | 113 | 3,600 |
| `keys: []` | 163 | 2,100 |

`keys` omitted means every property; `keys: []` means paths alone. The two compose.

### It slices, it does not parse

`contents` finds the opening `---`, finds the closing `---`, and emits the lines between
them. There is no YAML parser in the path, which is what buys the properties worth
having:

- Keys keep their authored order, quoting, and spacing.
- Malformed frontmatter passes through as written rather than being rejected or repaired.
- The output round-trips: what comes back is what is on disk.
- A property whose value is a `[[wikilink]]` is visibly an edge, because the value is
  right there. No classification pass is needed — see
  `plugins/hoplite-skills/references/frontmatter.md`.

What it costs: `contents` cannot filter or project. A tag predicate or field selection
would need real parsing. It also does not apply the derived defaults in the frontmatter
standard, so a document without a `title` key shows no title rather than one inferred
from its slug.

### There is no index file

The listing is computed on call, not stored. Nothing in the corpus has to be updated when
a document is added, and two contributors adding documents in parallel touch disjoint
files.

## Install

The server has no dependencies and no build step. `.mcp.json` runs the interpreter
directly — no shell, since Claude Code spawns MCP servers as processes and `sh` is absent
from the PATH on Windows. Set the plugin's **Python executable** option if `python3` is
not the right name on your machine; a wrong value shows up as a failed MCP connection
rather than a message, because the process never starts.

The corpus root is the working directory Claude Code launched in, so `under` paths are
repo-relative.

## Development

```sh
cd plugins/hoplite-mcp
python -m pytest
python -m ruff check .
python -m pyright
```

`src/hoplite_catalog/contents.py` is the pure core — slicing and rendering, no I/O beyond
one read function. `src/hoplite_catalog/server.py` is the stdio JSON-RPC host, hand-rolled
on the standard library because the tool needs nothing else. When the graph tools in
`docs/specs/hoplite-tool-api.md` land, the host is the layer to swap for the official MCP
SDK; the tool body knows nothing about transport.
