"""Tests for ``Graph.resolve_wikilink`` — wikilink target → canonical path."""

from __future__ import annotations

from hoplite.graph import Graph
from hoplite.models import Document


def _graph_with(path: str, *, aliases: dict[str, str] | None = None) -> Graph:
    g = Graph()
    g.documents[path] = Document(path=path, resolved=True)
    g.casefold_index[path.casefold()] = path
    for alias, canonical in (aliases or {}).items():
        g.aliases[alias] = canonical
    return g


def test_direct_path_resolves() -> None:
    g = _graph_with("notes/foo.md")
    assert g.resolve_wikilink("notes/foo.md") == "notes/foo.md"


def test_extension_omitted_resolves() -> None:
    g = _graph_with("notes/foo.md")
    assert g.resolve_wikilink("notes/foo") == "notes/foo.md"


def test_casefold_resolves() -> None:
    g = _graph_with("notes/foo.md")
    assert g.resolve_wikilink("Notes/Foo.MD") == "notes/foo.md"


def test_alias_resolves() -> None:
    g = _graph_with("notes/foo.md", aliases={"old-foo": "notes/foo.md"})
    assert g.resolve_wikilink("old-foo") == "notes/foo.md"


def test_missing_target_returns_none() -> None:
    g = _graph_with("notes/foo.md")
    assert g.resolve_wikilink("notes/missing") is None


def test_pipe_alias_stripped() -> None:
    # `[[hoplite/roadmap|roadmap.md]]` — pipe introduces display text;
    # resolution uses the target on the left.
    g = _graph_with("hoplite/roadmap.md")
    assert g.resolve_wikilink("hoplite/roadmap|roadmap.md") == "hoplite/roadmap.md"


def test_hash_anchor_stripped() -> None:
    # `[[hoplite/architecture#wikilinks]]` — anchor jumps to a section
    # but the target file is the part before `#`.
    g = _graph_with("hoplite/architecture.md")
    assert (
        g.resolve_wikilink("hoplite/architecture#wikilinks") == "hoplite/architecture.md"
    )


def test_anchor_and_alias_both_stripped() -> None:
    # `[[target#anchor|label]]` — both display modifiers drop out.
    g = _graph_with("hoplite/architecture.md")
    assert (
        g.resolve_wikilink("hoplite/architecture#dump-schema|architecture.md")
        == "hoplite/architecture.md"
    )


def test_alias_then_anchor_order_irrelevant() -> None:
    # Order of `#` and `|` shouldn't matter — the slice before the first `|`
    # is taken first, then the slice before the first `#`. A `#` inside the
    # alias text drops with it.
    g = _graph_with("hoplite/roadmap.md")
    assert g.resolve_wikilink("hoplite/roadmap|see #section") == "hoplite/roadmap.md"


def test_only_anchor_returns_none() -> None:
    # `[[#section]]` strips to an empty target — same-document anchor, not
    # a cross-document link. The walker should not materialize a ghost for it.
    g = _graph_with("notes/foo.md")
    assert g.resolve_wikilink("#section") is None


def test_only_alias_returns_none() -> None:
    g = _graph_with("notes/foo.md")
    assert g.resolve_wikilink("|just a label") is None


def test_stripped_target_then_extension_retry() -> None:
    # Alias/anchor strip, then `.md` retry — both transformations compose.
    g = _graph_with("hoplite/roadmap.md")
    assert g.resolve_wikilink("hoplite/roadmap#columnar|roadmap") == "hoplite/roadmap.md"
