"""Count the distinct frontmatter keys in a subtree of the corpus.

In SQL over an imaginary frontmatter table this is
``select key, count(*) from frontmatter group by key``. The report is one line per key,
``key: documents``, so a caller can see what the vocabulary is before spending a
``contents(keys=[...])`` call guessing at it.

The vocabulary is open by design — a new predicate is a doc change, not a schema
migration — so nothing here judges a key. A count is what keys exist and how widely each
is used; whether a key is a good one is a question for the glossary, not for a tally.

Values span lines, so the count reads the grouping in ``documents.group_properties``
rather than the ``key:`` lines. A block list puts the value on the indented lines below
the key, and a scanner reading raw lines would count each ``- "[[link]]"`` as a key of
its own.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import final

from hoplite_catalog.documents import Document

__all__ = ["KeyUse", "tally"]


@final
@dataclass(frozen=True, slots=True)
class KeyUse:
    """One frontmatter key and the number of documents carrying it."""

    key: str
    documents: int


def tally(documents: Iterable[Document]) -> tuple[KeyUse, ...]:
    """Count the documents carrying each frontmatter key, ordered by key.

    A key repeated within one document counts once: the number is documents, not
    occurrences, so it answers "how much of the corpus would ``keys: [status]`` return".

    A document that could not be read contributes nothing. It reports no properties, so
    the reason standing in for its frontmatter never enters the vocabulary.

    Ordering is alphabetical rather than by count, so two calls over an unchanged corpus
    return identical text and a caller looking for one key can scan for it.
    """
    counts = Counter(
        key for document in documents for key in {prop.key for prop in document.properties}
    )
    return tuple(KeyUse(key=key, documents=counts[key]) for key in sorted(counts))
