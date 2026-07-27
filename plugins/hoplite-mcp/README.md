# hoplite-mcp

The `catalog` MCP server, over a markdown corpus. Two tools. No dependencies, no build
step, Python 3.12 or newer. The corpus root is the working directory Claude Code launched
in, so paths are repo-relative.

## contents(under, keys)

Reports one folder in three groups, each under a `#` heading:

- `# directories` — the folder tree rooted at `under`, to full depth, each folder with the
  count of documents directly in it.
- `# other files` — the non-markdown files in `under`.
- `# documents` — the documents in `under` alone, each followed by its frontmatter lines as
  written, comments dropped.

The `#` marks a heading. A blank line can't, because blank lines also separate two
documents inside `# documents`.

A frontmatter key can never start with `#`. A path can: paths are corpus-relative, so one
inside a folder always leads with that folder, but a file sitting at the corpus root leads
with its own name. So a root-level `#hash.md` prints a line starting with `#`, and a
root-level file named exactly `# documents` prints a line identical to a heading.

Frontmatter comments are dropped: printed as written, a `#` line would read as a heading.
Nothing else in a block is touched.

Directories recurse, documents do not. Hidden folders are not walked into and hidden files
are not listed, though naming a hidden folder as `under` works. A hidden `.md` file is
still a document. A folder linking outside the corpus prints `links outside the corpus`
where its count would be, and a non-markdown file linking outside prints it after the path:

```
  external/ links outside the corpus
notes/leak.pdf links outside the corpus
```

A folder that cannot be read prints `cannot be listed` where its count would be. It is not
walked into, so nothing under it is listed:

```
  closed/ cannot be listed
```

A folder linking to another folder inside the corpus is walked, and its documents are
reported under the link path. A document reachable by two paths is listed once, under the
first path reached, so `vocabulary` counts it once. Each folder counts what sits in it, so
a mirrored document is counted twice and the folder counts will not add up to the document
count. A link back to an ancestor terminates.

Skipping hidden folders is the only bound on the walk. Folders without a leading dot are
walked to full depth, `__pycache__`, `node_modules`, and a dotless `venv` included. Naming
a hidden folder as `under` walks its non-hidden children to full depth. There is no cap on
the number of folders reported.

`under` defaults to the corpus root. `keys` picks which frontmatter properties to emit:
omit it for all of them, `[]` for paths alone.

```
contents(under="notes")

# directories (documents directly in each)
notes/ 0
  external/ links outside the corpus
  travel/ 2

# other files
notes/scan.pdf

# documents
none
```

## vocabulary(under)

Reports one `key: documents` line per frontmatter key, ordered by key. The number is how
many documents carry that key. Recurses, skipping hidden folders. `under` defaults to the
corpus root.

## Errors

Both tools return an error, and no report, when `under` names nothing, sits outside the
corpus root, resolves outside it through a link, or names a file that is not `.md`. Only
markdown is ever opened: a `.env` or a lockfile that happens to start with `---` is refused
by name, not sliced. The argument checks do the same:
`under` must be a string, `keys` a list of strings. `contents` also errors when `keys` names no
property carried by any document that has frontmatter. A folder whose documents have no
frontmatter at all is not that case, and lists normally.

A document that cannot be read is reported instead of failing the call. It keeps its place
in `# documents` and prints the path and the reason, where its frontmatter would be:

```
notes/leak.md
links to a target outside the corpus
```

The other reason is `cannot be read (...)`, carrying the operating system's message.

## Install

Set the plugin's **Python executable** option if `python3` is not the right name on your
machine, or is older than 3.12. The symptom either way is a failed MCP connection rather
than a message.

## Development

```sh
cd plugins/hoplite-mcp
pip install -e .[dev]
python -m pytest
python -m ruff check .
python -m pyright
```

The dev extra installs the test and lint tools. The server itself has no dependencies.
`pytest` needs the extra because coverage runs on every test run.

`ports.py` holds the `Files` port. `adapters.py` holds `RealFiles`, the pathlib
implementation, and is the only code that touches a filesystem; an import-linter contract
keeps the core from importing it, so the port cannot be bypassed. `contents.py` holds the
walking, slicing, and rendering. It takes a `Files` as its first argument, so a test hands
it an in-memory corpus and drives the cases a real filesystem will not reliably produce.
`vocabulary.py` counts keys over what it collects. `server.py` is the stdio JSON-RPC host,
hand-rolled on the standard library. The graph tools designed in
`docs/specs/hoplite-tool-api.md` register here when they land.
