# Negation grep

Search for negation trigger words. Each hit is a candidate for positive rewrite under the golden rule (`Prefer positively framed assertions`).

## The trigger list

`not`, `don't`, `didn't`, `wasn't`, `won't`, `can't`, `cannot`, `never`, `avoid`, `should not`, plus phrase patterns `didn't seem`, `wasn't very`.

## How to apply

1. Grep for each trigger word in the page.
2. For each hit, ask: "What is this sentence actually trying to say?"
3. Rewrite to state that directly. See [positive-transforms.md](positive-transforms.md) for transform examples.

## When to keep the negation

- The constraint is named by its negation in the trade (the well-established idiom).
- The positive label is more confusing than the natural negative.
- A list of examples uses "avoid" as a label for things to recognize.
- Otherwise, rewrite positively.
