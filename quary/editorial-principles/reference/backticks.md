# Backticks

Code, paths, identifiers, and CLI commands go in backticks. Multi-line code samples go in fenced code blocks with the language tag.

## How to apply

- Inline: `\`function_name\``, `\`path/to/file.md\``, `\`--flag\``, `\`SELECT * FROM ...\``.
- Multi-line: triple-backtick fence with a language tag (`bash`, `python`, `markdown`, `json`, etc.).
- File paths in backticks; URLs as markdown links.

## What this signals

- Backticks tell the reader (human or LLM) "this is literal, not prose." Copy-paste-able.
- A path or identifier in prose without backticks reads as a word and gets glossed over.
