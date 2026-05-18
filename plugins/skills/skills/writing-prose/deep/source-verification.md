# Source verification

For any claim about behavior, verify against the actual source (code, schema, document); update one if they disagree.

## How to apply

- Identify behavioral claims in the prose.
- For each, find the corresponding source: the function, the configuration line, the schema definition.
- Confirm the prose matches the source.
- If they disagree, update whichever is wrong (usually the prose).

## When this matters most

- After a rename or refactor (pair with **Rename propagation**).
- After a behavior change (the code shifted; the docs may not have caught up).
- When the prose makes specific claims about edge cases that the source would settle.

## Related

- The author-side counterpart of this check is **Source is the authority** in Composition.
