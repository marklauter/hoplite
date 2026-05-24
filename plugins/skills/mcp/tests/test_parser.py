"""Tests for hoplite.parser."""

from __future__ import annotations

import pytest

from hoplite.parser import (
    And,
    Label,
    Not,
    Or,
    ParseError,
    compile,  # noqa: A004 — mirrors the parser's public API name; see parser.py
    parse,
    parse_predicate,
)

# --- AST construction ---------------------------------------------------------


def test_single_label() -> None:
    assert parse("note") == Label("note")


def test_label_with_digits_and_hyphen() -> None:
    assert parse("2026-05-24") == Label("2026-05-24")


def test_and_operator() -> None:
    assert parse("a & b") == And(Label("a"), Label("b"))


def test_or_operator() -> None:
    assert parse("a | b") == Or(Label("a"), Label("b"))


def test_not_operator() -> None:
    assert parse("!a") == Not(Label("a"))


def test_double_negation_chain() -> None:
    assert parse("!!a") == Not(Not(Label("a")))


def test_triple_negation_chain() -> None:
    assert parse("!!!a") == Not(Not(Not(Label("a"))))


def test_no_whitespace_required() -> None:
    assert parse("a&b|c") == Or(And(Label("a"), Label("b")), Label("c"))


def test_extra_whitespace_ignored() -> None:
    assert parse("  a  &  b  ") == And(Label("a"), Label("b"))


# --- precedence and associativity ---------------------------------------------


def test_and_binds_tighter_than_or() -> None:
    # a & b | c -> (a & b) | c
    assert parse("a & b | c") == Or(And(Label("a"), Label("b")), Label("c"))


def test_or_does_not_bind_tighter_than_and() -> None:
    # a | b & c -> a | (b & c)
    assert parse("a | b & c") == Or(Label("a"), And(Label("b"), Label("c")))


def test_not_binds_tighter_than_and() -> None:
    # !a & b -> (!a) & b
    assert parse("!a & b") == And(Not(Label("a")), Label("b"))


def test_not_binds_tighter_than_or() -> None:
    assert parse("!a | b") == Or(Not(Label("a")), Label("b"))


def test_and_left_associative() -> None:
    # a & b & c -> (a & b) & c
    assert parse("a & b & c") == And(And(Label("a"), Label("b")), Label("c"))


def test_or_left_associative() -> None:
    assert parse("a | b | c") == Or(Or(Label("a"), Label("b")), Label("c"))


def test_parens_override_precedence() -> None:
    # a & (b | c) -> And(a, Or(b, c))
    assert parse("a & (b | c)") == And(Label("a"), Or(Label("b"), Label("c")))


def test_nested_parens() -> None:
    assert parse("((a))") == Label("a")


def test_doc_example_compound() -> None:
    # (note | journal) & !draft
    assert parse("(note | journal) & !draft") == And(
        Or(Label("note"), Label("journal")),
        Not(Label("draft")),
    )


# --- error paths --------------------------------------------------------------


def test_empty_input_raises() -> None:
    with pytest.raises(ParseError) as exc:
        parse("")
    assert exc.value.message == "empty input"
    assert exc.value.position == 0
    assert exc.value.text == ""


def test_whitespace_only_input_raises() -> None:
    with pytest.raises(ParseError) as exc:
        parse("   ")
    assert exc.value.message == "empty input"


def test_unexpected_char_raises_with_position() -> None:
    with pytest.raises(ParseError) as exc:
        parse("a & @ b")
    assert exc.value.position == 4
    assert "@" in exc.value.message
    assert "column 5" in str(exc.value)


def test_dangling_and_operator() -> None:
    with pytest.raises(ParseError) as exc:
        parse("a &")
    # After consuming '&' (pos=2) and skipping ws (pos=3), atom sees EOF.
    assert exc.value.position == 3
    assert "unexpected end of input" in exc.value.message


def test_dangling_or_operator() -> None:
    with pytest.raises(ParseError):
        parse("a |")


def test_dangling_not_operator() -> None:
    with pytest.raises(ParseError):
        parse("!")


def test_unclosed_paren() -> None:
    with pytest.raises(ParseError) as exc:
        parse("(a & b")
    assert "expected ')'" in exc.value.message


def test_unclosed_paren_nested() -> None:
    with pytest.raises(ParseError):
        parse("((a)")


def test_unexpected_close_paren() -> None:
    with pytest.raises(ParseError) as exc:
        parse("a)")
    # Top-level sees trailing ')' as junk after expression.
    assert ")" in exc.value.message


def test_leading_operator() -> None:
    with pytest.raises(ParseError):
        parse("& a")


def test_invalid_label_char_uppercase() -> None:
    # Uppercase is not in [a-z0-9-]; the parser stops at 'A' and reports it.
    with pytest.raises(ParseError) as exc:
        parse("Abc")
    assert exc.value.position == 0


def test_invalid_label_char_underscore() -> None:
    with pytest.raises(ParseError) as exc:
        parse("a_b")
    assert exc.value.position == 1


def test_empty_parens() -> None:
    with pytest.raises(ParseError):
        parse("()")


def test_parse_error_payload_fields() -> None:
    text = "a & @"
    with pytest.raises(ParseError) as exc:
        parse(text)
    err = exc.value
    assert err.text == text
    assert err.position == 4
    assert isinstance(err.position, int)
    assert isinstance(err, ValueError)  # subclass contract


# --- compiled predicate evaluation -------------------------------------------


@pytest.mark.parametrize(
    ("expression", "labels", "expected"),
    [
        # single label
        ("note", frozenset({"note"}), True),
        ("note", frozenset({"journal"}), False),
        ("note", frozenset[str](), False),
        # AND
        ("note & mcp", frozenset({"note", "mcp"}), True),
        ("note & mcp", frozenset({"note"}), False),
        ("note & mcp", frozenset({"mcp"}), False),
        ("note & mcp", frozenset[str](), False),
        # OR
        ("note | journal", frozenset({"note"}), True),
        ("note | journal", frozenset({"journal"}), True),
        ("note | journal", frozenset({"note", "journal"}), True),
        ("note | journal", frozenset({"draft"}), False),
        # NOT
        ("!draft", frozenset({"note"}), True),
        ("!draft", frozenset({"draft"}), False),
        ("!draft", frozenset({"note", "draft"}), False),
        # double negation
        ("!!note", frozenset({"note"}), True),
        ("!!note", frozenset[str](), False),
        # precedence: a & b | c == (a & b) | c
        ("a & b | c", frozenset({"a", "b"}), True),
        ("a & b | c", frozenset({"c"}), True),
        ("a & b | c", frozenset({"a"}), False),
        ("a & b | c", frozenset({"b"}), False),
        # parens override
        ("a & (b | c)", frozenset({"a", "b"}), True),
        ("a & (b | c)", frozenset({"a", "c"}), True),
        ("a & (b | c)", frozenset({"b", "c"}), False),
        ("a & (b | c)", frozenset({"a"}), False),
        # doc compound: (note | journal) & !draft
        ("(note | journal) & !draft", frozenset({"note"}), True),
        ("(note | journal) & !draft", frozenset({"journal"}), True),
        ("(note | journal) & !draft", frozenset({"note", "draft"}), False),
        ("(note | journal) & !draft", frozenset({"draft"}), False),
        ("(note | journal) & !draft", frozenset({"mcp"}), False),
        # doc compound: mcp & !2026-05-24
        ("mcp & !2026-05-24", frozenset({"mcp"}), True),
        ("mcp & !2026-05-24", frozenset({"mcp", "2026-05-24"}), False),
        ("mcp & !2026-05-24", frozenset({"2026-05-24"}), False),
    ],
)
def test_compiled_predicate(expression: str, labels: frozenset[str], expected: bool) -> None:
    predicate = parse_predicate(expression)
    assert predicate(labels) is expected


def test_compile_directly_from_ast() -> None:
    # compile() accepts a hand-built AST, not just parser output.
    ast = And(Label("a"), Not(Label("b")))
    predicate = compile(ast)
    assert predicate(frozenset({"a"})) is True
    assert predicate(frozenset({"a", "b"})) is False


def test_parse_predicate_round_trip() -> None:
    predicate = parse_predicate("a | b")
    assert predicate(frozenset({"a"})) is True
    assert predicate(frozenset({"b"})) is True
    assert predicate(frozenset[str]()) is False
