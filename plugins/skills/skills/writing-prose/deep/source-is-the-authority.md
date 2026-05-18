# Source is the authority

The document defers to the system it describes. Read the source — code, configuration, schema, behavior — before writing about it. When prose and source disagree, fix the prose. When a term, file path, or identifier changes, every document mentioning it goes stale; update them in the same change set.

## How to apply

- Read the source before writing about it — the file, the function, the schema, the command output. Documenting from memory is the most common way prose drifts from reality.
- When the doc and the source disagree, fix the doc. Update prose, not behavior.
- On renames and refactors, grep the entire project for the old name or path before declaring the change done. Update every reference in the same change set.
- Cite by stable reference — function name, symbol, heading anchor — not by line number. Line numbers drift on every edit; symbols and headings persist.
