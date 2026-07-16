# Tense drift grep

Search for the words *will* and *would*. Most uses are tense drift — replace with present tense.

## How to apply

- Grep for `\bwill\b` and `\bwould\b` in the page.
- For each hit, ask: is this a current behavior described in future tense?
- If yes, rewrite in present tense ("the function will return" → "the function returns").

## When to keep

- Genuine future-tense claims about scheduled work ("the migration will run on Thursday").
- Conditional *would* in arguments ("if the cache misses, the latency would spike").
- Otherwise, rewrite in present tense.
