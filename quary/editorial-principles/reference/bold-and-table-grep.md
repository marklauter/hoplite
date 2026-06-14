# Bold and table grep

Search for `**` (markdown bold) and `|---|` (tables). Both should return zero hits except in worked examples that demonstrate what to remove.

## How to apply

- Grep for `\*\*` and `\|---\|` in the page.
- Expect zero hits.
- Any hit not inside a worked example demonstrating what to remove is a defect; remove the bold or convert the table to headings and bullets.

## When to keep

- Worked example that demonstrates the violation (one hit per demonstration).
- Otherwise, never.
