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
  written, less its comments.

The `#` is what separates a heading from content. A blank line does double duty — it
divides the groups and also divides two documents inside `# documents` — so the heading is
the only group boundary.

A frontmatter key can never start with `#`. A path can: paths are corpus-relative, so one
inside a folder always leads with that folder, but a file sitting at the corpus root leads
with its own name. A root-level `#hash.md` therefore emits a line starting with `#`, and a
root-level file named exactly `# documents` emits a line identical to a heading.

A frontmatter comment is dropped, since a `#` line emitted verbatim would read as a
heading. Nothing else in a block is touched.

Directories recurse, documents do not. Hidden folders are not walked into and hidden files
are not listed, though naming a hidden folder as `under` works. A hidden `.md` file is
still a document. A folder linking outside the corpus takes the place of its count,
and a non-markdown file linking outside is marked the same way:

```
  external/ links outside the corpus
notes/leak.pdf links outside the corpus
```

A folder that cannot be read takes the place of its count the same way, and is not walked
into, so nothing under it is listed:

```
  closed/ cannot be listed
```

A folder linking to another folder inside the corpus is walked, and its documents are
reported under the link path. A document reachable by two paths is listed once, under the
first path reached, so `vocabulary` counts it once. The folder counts are per folder, so
the same document is counted in both — subtree counts do not sum to the document count
when a folder is mirrored. A link back to an ancestor terminates.

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

Reports one `key: documents` line per distinct frontmatter key, ordered by key, where the
number is how many documents carry it. Recurses, skipping hidden folders. `under` defaults
to the corpus root.

## Errors

Both tools return an error, and no report, when `under` names nothing, sits outside the
corpus root, or resolves outside it through a link. So do the argument checks: `under`
must be a string, `keys` a list of strings. `contents` also errors when `keys` names no
property carried by any document that has frontmatter — a folder whose documents have no
frontmatter at all is not that case, and lists normally.

A document that cannot be read is reported rather than raised. It keeps its place in
`# documents`, with the reason where its frontmatter would be:

```
notes/leak.md
links to a target outside the corpus
```

The other reason is `cannot be read (...)`, carrying the operating system's message. One
bad document does not cost the caller the folder.

## Install

Set the plugin's **Python executable** option if `python3` is not the right name on your
machine, or is older than 3.12. The symptom either way is a failed MCP connection rather
than a message.

## Development

```sh
cd plugins/hoplite-mcp
python -m pytest
python -m ruff check .
python -m pyright
```

`contents.py` holds the walking, slicing, and rendering. Directory access is spread across
its walking functions, through `iterdir`, `glob`, `resolve`, and `is_dir`; `read_entry` is
the only function that opens a file.
`vocabulary.py` counts keys over what it collects. `server.py` is the stdio JSON-RPC host,
hand-rolled on the standard library, and the layer to swap for the MCP SDK when the graph
tools in `docs/specs/hoplite-tool-api.md` land.
