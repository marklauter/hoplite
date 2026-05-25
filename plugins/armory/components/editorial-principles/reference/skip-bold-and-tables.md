# Skip bold and tables

Bold adds noise without changing how a reader (human or LLM) processes the text. Tables are unreadable in source form and add no value over headings and bullets.

## How to apply

- No `**bold**` in prose. Headings, lists, and prose carry structure on their own.
- No markdown tables. Convert to headings and bullets:

  Before:

  ```markdown
  | Name | Purpose |
  |---|---|
  | foo | does X |
  | bar | does Y |
  ```

  After:

  ```markdown
  ### foo
  Does X.

  ### bar
  Does Y.
  ```

## When to keep

- A worked example that demonstrates the violation (one hit per demonstration). The example shows the antipattern so the reader recognizes it.
- Otherwise, never.
