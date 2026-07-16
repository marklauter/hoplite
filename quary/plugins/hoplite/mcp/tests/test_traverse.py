"""Unit tests for ``tools.traverse_nodes`` — BFS over the in-memory graph.

Tests build a synthetic :class:`Graph` directly (no walker, no FTS, no MinHash)
and exercise each branch of the traversal predicate independently:

- depth correctness (1, 2, 3+; origin always excluded)
- BFS invariants (visited dedup, shortest path wins in diamonds, cycle short-circuit)
- ``via_edges`` path reconstruction
- ``edge_types`` filter (mentions only, related only, omitted = all)
- ``direction`` filter (out / in / both)
- ``top_k_related`` cap on ranked related edges (mentions/cites always followed)
- ``tagged`` predicate against ``document_properties``
- ghost-target reachability
- disconnected origin → empty result
- unknown origin → ValueError
- ``depth < 1`` → ValueError
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from hoplite import tools
from hoplite.graph import Graph
from hoplite.models import Document, Edge
from hoplite.tools import TraversePredicate


@pytest.fixture(autouse=True)
def _reset_tools_graph() -> Iterator[None]:  # pyright: ignore[reportUnusedFunction]
    """Tools.py keeps the graph in a module-level singleton; clear between tests."""
    yield
    tools._graph = None  # pyright: ignore[reportPrivateUsage]


def _add_node(
    graph: Graph,
    path: str,
    *,
    tags: list[str] | None = None,
    resolved: bool = True,
) -> None:
    graph.documents[path] = Document(path=path, resolved=resolved)
    graph.casefold_index[path.casefold()] = path
    if resolved:
        props: dict[str, list[str]] = {
            "title": [path],
            "summary": [f"summary of {path}"],
        }
        if tags:
            props["tags"] = list(tags)
        graph.document_properties[path] = props


def _add_edge(
    graph: Graph,
    src: str,
    dst: str,
    kind: str,
    confidence: float = 1.0,
) -> None:
    graph.add_edge(Edge(src=src, dst=dst, kind=kind, confidence=confidence))


def _install(graph: Graph) -> None:
    tools._graph = graph  # pyright: ignore[reportPrivateUsage]


# ---------- linear chain: a → b → c → d ----------


@pytest.fixture
def linear_graph() -> Graph:
    g = Graph()
    for name in ("a", "b", "c", "d"):
        _add_node(g, name)
    _add_edge(g, "a", "b", "mentions")
    _add_edge(g, "b", "c", "mentions")
    _add_edge(g, "c", "d", "mentions")
    return g


def test_depth_1_reaches_immediate_neighbor(linear_graph: Graph) -> None:
    _install(linear_graph)
    hits = tools.traverse_nodes(from_="a", depth=1)
    assert [h.path for h in hits] == ["b"]
    assert hits[0].distance == 1
    assert len(hits[0].via_edges) == 1
    edge = hits[0].via_edges[0]
    assert (edge.src, edge.dst, edge.kind) == ("a", "b", "mentions")


def test_depth_2_reaches_two_hops(linear_graph: Graph) -> None:
    _install(linear_graph)
    hits = tools.traverse_nodes(from_="a", depth=2)
    assert {h.distance: h.path for h in hits} == {1: "b", 2: "c"}


def test_depth_3_walks_full_chain(linear_graph: Graph) -> None:
    _install(linear_graph)
    hits = tools.traverse_nodes(from_="a", depth=3)
    assert {h.distance: h.path for h in hits} == {1: "b", 2: "c", 3: "d"}


def test_origin_excluded_from_results(linear_graph: Graph) -> None:
    _install(linear_graph)
    hits = tools.traverse_nodes(from_="a", depth=5)
    assert "a" not in [h.path for h in hits]


def test_via_edges_reconstructs_path(linear_graph: Graph) -> None:
    _install(linear_graph)
    hits = tools.traverse_nodes(from_="a", depth=3)
    d_hit = next(h for h in hits if h.path == "d")
    assert [(e.src, e.dst) for e in d_hit.via_edges] == [
        ("a", "b"),
        ("b", "c"),
        ("c", "d"),
    ]


# ---------- cycle: a → b → c → a ----------


@pytest.fixture
def cycle_graph() -> Graph:
    g = Graph()
    for name in ("a", "b", "c"):
        _add_node(g, name)
    _add_edge(g, "a", "b", "mentions")
    _add_edge(g, "b", "c", "mentions")
    _add_edge(g, "c", "a", "mentions")
    return g


def test_cycle_short_circuits_on_visited(cycle_graph: Graph) -> None:
    _install(cycle_graph)
    hits = tools.traverse_nodes(from_="a", depth=10)
    # a is excluded (origin); b reachable at 1, c reachable at 2; cycle back to a dropped.
    assert {h.distance: h.path for h in hits} == {1: "b", 2: "c"}


def test_self_loop_dropped() -> None:
    """a → a plus a → b. The self-loop must not produce a hit for a itself."""
    g = Graph()
    _add_node(g, "a")
    _add_node(g, "b")
    _add_edge(g, "a", "a", "mentions")
    _add_edge(g, "a", "b", "mentions")
    _install(g)
    hits = tools.traverse_nodes(from_="a", depth=5)
    assert [h.path for h in hits] == ["b"]
    assert "a" not in [h.path for h in hits]


def test_two_node_cycle_visits_each_once() -> None:
    """a ↔ b (two-edge cycle). b reached once at distance 1; cycle back to a dropped."""
    g = Graph()
    _add_node(g, "a")
    _add_node(g, "b")
    _add_edge(g, "a", "b", "mentions")
    _add_edge(g, "b", "a", "mentions")
    _install(g)
    hits = tools.traverse_nodes(from_="a", depth=5)
    assert [h.path for h in hits] == ["b"]


def test_mid_graph_cycle_not_through_origin() -> None:
    """a → b → c → b (cycle between b and c, not touching origin a).

    b reached at distance 1 from a; c at distance 2 via b; the c→b cycle-back
    is dropped because b is already in visited.
    """
    g = Graph()
    for name in ("a", "b", "c"):
        _add_node(g, name)
    _add_edge(g, "a", "b", "mentions")
    _add_edge(g, "b", "c", "mentions")
    _add_edge(g, "c", "b", "mentions")
    _install(g)
    hits = tools.traverse_nodes(from_="a", depth=10)
    assert {h.distance: h.path for h in hits} == {1: "b", 2: "c"}
    # b appears exactly once; c appears exactly once.
    counts = {h.path: 1 for h in hits}
    assert sum(counts.values()) == len(hits)


# ---------- diamond: a → b, a → c, b → d, c → d ----------


@pytest.fixture
def diamond_graph() -> Graph:
    g = Graph()
    for name in ("a", "b", "c", "d"):
        _add_node(g, name)
    _add_edge(g, "a", "b", "mentions")
    _add_edge(g, "a", "c", "mentions")
    _add_edge(g, "b", "d", "mentions")
    _add_edge(g, "c", "d", "mentions")
    return g


def test_diamond_d_reached_once_at_shortest_distance(diamond_graph: Graph) -> None:
    _install(diamond_graph)
    hits = tools.traverse_nodes(from_="a", depth=3)
    d_hits = [h for h in hits if h.path == "d"]
    assert len(d_hits) == 1, "d should appear exactly once despite two reaching paths"
    assert d_hits[0].distance == 2


# ---------- mixed edge kinds: a -mentions→ b, a ↔related↔ c ----------


@pytest.fixture
def kinded_graph() -> Graph:
    g = Graph()
    for name in ("a", "b", "c"):
        _add_node(g, name)
    _add_edge(g, "a", "b", "mentions")
    _add_edge(g, "a", "c", "related", confidence=0.8)
    _add_edge(g, "c", "a", "related", confidence=0.8)
    return g


def test_edge_types_filter_mentions_only(kinded_graph: Graph) -> None:
    _install(kinded_graph)
    hits = tools.traverse_nodes(
        from_="a",
        predicate=TraversePredicate(edge_types=["mentions"]),
        depth=1,
    )
    assert [h.path for h in hits] == ["b"]


def test_edge_types_filter_related_only(kinded_graph: Graph) -> None:
    _install(kinded_graph)
    hits = tools.traverse_nodes(
        from_="a",
        predicate=TraversePredicate(edge_types=["related"]),
        depth=1,
    )
    assert [h.path for h in hits] == ["c"]


def test_edge_types_omitted_follows_all_kinds(kinded_graph: Graph) -> None:
    _install(kinded_graph)
    hits = tools.traverse_nodes(from_="a", depth=1)
    assert sorted(h.path for h in hits) == ["b", "c"]


# ---------- cites edge: a -cites→ https://example.com ----------


@pytest.fixture
def cites_graph() -> Graph:
    g = Graph()
    _add_node(g, "a")
    _add_node(g, "https://example.com", resolved=False)
    _add_edge(g, "a", "https://example.com", "cites")
    return g


def test_edge_types_filter_cites_only(cites_graph: Graph) -> None:
    _install(cites_graph)
    hits = tools.traverse_nodes(
        from_="a",
        predicate=TraversePredicate(edge_types=["cites"]),
        depth=1,
    )
    assert [h.path for h in hits] == ["https://example.com"]


# ---------- direction: b -mentions→ a -mentions→ c ----------


@pytest.fixture
def directional_graph() -> Graph:
    g = Graph()
    for name in ("a", "b", "c"):
        _add_node(g, name)
    _add_edge(g, "b", "a", "mentions")
    _add_edge(g, "a", "c", "mentions")
    return g


def test_direction_out_follows_outbound_only(directional_graph: Graph) -> None:
    _install(directional_graph)
    hits = tools.traverse_nodes(from_="a", predicate=TraversePredicate(direction="out"), depth=1)
    assert [h.path for h in hits] == ["c"]


def test_direction_in_follows_inbound_only(directional_graph: Graph) -> None:
    _install(directional_graph)
    hits = tools.traverse_nodes(from_="a", predicate=TraversePredicate(direction="in"), depth=1)
    assert [h.path for h in hits] == ["b"]


def test_direction_both_follows_both(directional_graph: Graph) -> None:
    _install(directional_graph)
    hits = tools.traverse_nodes(from_="a", predicate=TraversePredicate(direction="both"), depth=1)
    assert sorted(h.path for h in hits) == ["b", "c"]


# ---------- top_k_related: a related→ b (0.9), c (0.5), d (0.3) ----------


@pytest.fixture
def ranked_graph() -> Graph:
    g = Graph()
    for name in ("a", "b", "c", "d"):
        _add_node(g, name)
    _add_edge(g, "a", "b", "related", confidence=0.9)
    _add_edge(g, "a", "c", "related", confidence=0.5)
    _add_edge(g, "a", "d", "related", confidence=0.3)
    return g


def test_top_k_related_caps_neighbors(ranked_graph: Graph) -> None:
    _install(ranked_graph)
    hits = tools.traverse_nodes(from_="a", predicate=TraversePredicate(top_k_related=2), depth=1)
    assert sorted(h.path for h in hits) == ["b", "c"]


def test_top_k_related_unset_returns_all(ranked_graph: Graph) -> None:
    _install(ranked_graph)
    hits = tools.traverse_nodes(from_="a", predicate=TraversePredicate(), depth=1)
    assert sorted(h.path for h in hits) == ["b", "c", "d"]


def test_top_k_related_does_not_cap_mentions() -> None:
    g = Graph()
    for name in ("a", "m1", "m2", "m3", "r1", "r2"):
        _add_node(g, name)
    _add_edge(g, "a", "m1", "mentions")
    _add_edge(g, "a", "m2", "mentions")
    _add_edge(g, "a", "m3", "mentions")
    _add_edge(g, "a", "r1", "related", confidence=0.9)
    _add_edge(g, "a", "r2", "related", confidence=0.4)
    _install(g)
    hits = tools.traverse_nodes(from_="a", predicate=TraversePredicate(top_k_related=1), depth=1)
    assert sorted(h.path for h in hits) == ["m1", "m2", "m3", "r1"]


# ---------- tagged predicate ----------


@pytest.fixture
def tagged_graph() -> Graph:
    g = Graph()
    _add_node(g, "a", tags=[])
    _add_node(g, "b", tags=["keep"])
    _add_node(g, "c", tags=["skip"])
    _add_edge(g, "a", "b", "mentions")
    _add_edge(g, "a", "c", "mentions")
    return g


def test_tagged_predicate_filters_reached_nodes(tagged_graph: Graph) -> None:
    _install(tagged_graph)
    hits = tools.traverse_nodes(from_="a", predicate=TraversePredicate(tagged="keep"), depth=1)
    assert [h.path for h in hits] == ["b"]


def test_tagged_predicate_excludes_all_when_no_match(tagged_graph: Graph) -> None:
    _install(tagged_graph)
    hits = tools.traverse_nodes(from_="a", predicate=TraversePredicate(tagged="absent"), depth=1)
    assert hits == []


# ---------- ghost reachability ----------


def test_ghost_neighbor_is_reachable() -> None:
    g = Graph()
    _add_node(g, "a")
    g.documents["ghost"] = Document(path="ghost", resolved=False)
    g.casefold_index["ghost"] = "ghost"
    _add_edge(g, "a", "ghost", "mentions")
    _install(g)
    hits = tools.traverse_nodes(from_="a", depth=1)
    assert [h.path for h in hits] == ["ghost"]


# ---------- edge cases ----------


def test_disconnected_origin_returns_empty() -> None:
    g = Graph()
    _add_node(g, "lonely")
    _install(g)
    assert tools.traverse_nodes(from_="lonely", depth=5) == []


def test_unknown_origin_raises_value_error() -> None:
    _install(Graph())
    with pytest.raises(ValueError, match="unknown starting document"):
        tools.traverse_nodes(from_="missing", depth=1)


def test_depth_zero_raises_value_error() -> None:
    g = Graph()
    _add_node(g, "a")
    _install(g)
    with pytest.raises(ValueError, match="depth must be >= 1"):
        tools.traverse_nodes(from_="a", depth=0)


# ---------- result shape: summary and tags come from document_properties ----------


def test_hit_summary_and_tags_come_from_properties() -> None:
    g = Graph()
    _add_node(g, "a")
    _add_node(g, "b", tags=["foo", "bar"])
    _add_edge(g, "a", "b", "mentions")
    _install(g)
    hits = tools.traverse_nodes(from_="a", depth=1)
    assert len(hits) == 1
    hit = hits[0]
    assert hit.path == "b"
    assert hit.summary == "summary of b"
    assert hit.tags == ["bar", "foo"]  # sorted by tools.traverse_nodes
