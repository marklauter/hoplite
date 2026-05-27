"""Label expression parser.

Grammar (per docs/hoplite/hoplite-architecture.md#tag-predicates):

    expr     ::= or_expr
    or_expr  ::= and_expr ( '|' and_expr )*
    and_expr ::= not_expr ( '&' not_expr )*
    not_expr ::= '!' not_expr | atom
    atom     ::= label | '(' expr ')'
    label    ::= [a-z0-9-]+

Precedence: `!` binds tightest, then `&`, then `|`; `&` and `|` are
left-associative. Whitespace between tokens is permitted and ignored.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final, TypeAlias

__all__ = [
    "And",
    "Label",
    "LabelExpr",
    "Not",
    "Or",
    "ParseError",
    "compile",
    "parse",
    "parse_predicate",
]


@dataclass(frozen=True, slots=True)
class Label:
    name: str


@dataclass(frozen=True, slots=True)
class Not:
    operand: LabelExpr


@dataclass(frozen=True, slots=True)
class And:
    left: LabelExpr
    right: LabelExpr


@dataclass(frozen=True, slots=True)
class Or:
    left: LabelExpr
    right: LabelExpr


LabelExpr: TypeAlias = And | Or | Not | Label


class ParseError(ValueError):
    """Raised when a label expression fails to parse.

    Carries the original input, the byte position of the failure, and a
    one-line message. Position is zero-indexed; the rendered message
    reports the one-indexed column for human readers.
    """

    def __init__(self, text: str, position: int, message: str) -> None:
        super().__init__(f"{message} at column {position + 1}")
        self.text = text
        self.position = position
        self.message = message


_LABEL_CHARS: Final = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")
_WHITESPACE: Final = frozenset(" \t\n\r")


class _Parser:
    __slots__ = ("pos", "text")

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def _skip_ws(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in _WHITESPACE:
            self.pos += 1

    def _peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def _fail(self, message: str) -> ParseError:
        return ParseError(self.text, self.pos, message)

    def parse_expr(self) -> LabelExpr:
        return self._parse_or()

    def _parse_or(self) -> LabelExpr:
        node = self._parse_and()
        self._skip_ws()
        while self._peek() == "|":
            self.pos += 1
            right = self._parse_and()
            node = Or(node, right)
            self._skip_ws()
        return node

    def _parse_and(self) -> LabelExpr:
        node = self._parse_not()
        self._skip_ws()
        while self._peek() == "&":
            self.pos += 1
            right = self._parse_not()
            node = And(node, right)
            self._skip_ws()
        return node

    def _parse_not(self) -> LabelExpr:
        self._skip_ws()
        if self._peek() == "!":
            self.pos += 1
            return Not(self._parse_not())
        return self._parse_atom()

    def _parse_atom(self) -> LabelExpr:
        self._skip_ws()
        ch = self._peek()
        if ch == "":
            raise self._fail("unexpected end of input")
        if ch == "(":
            self.pos += 1
            node = self.parse_expr()
            self._skip_ws()
            if self._peek() != ")":
                raise self._fail("expected ')'")
            self.pos += 1
            return node
        if ch in _LABEL_CHARS:
            start = self.pos
            while self.pos < len(self.text) and self.text[self.pos] in _LABEL_CHARS:
                self.pos += 1
            return Label(self.text[start : self.pos])
        raise self._fail(f"unexpected {ch!r}")

    def parse_top(self) -> LabelExpr:
        expr = self.parse_expr()
        self._skip_ws()
        if self.pos < len(self.text):
            raise self._fail(f"unexpected {self._peek()!r}")
        return expr


def parse(text: str) -> LabelExpr:
    """Parse a label expression into an AST.

    Raises ParseError on empty input, unexpected characters, dangling
    operators, unclosed parentheses, or trailing junk after the expression.
    """
    if not text or not text.strip():
        raise ParseError(text, 0, "empty input")
    return _Parser(text).parse_top()


def _compile_label(name: str) -> Callable[[frozenset[str]], bool]:
    def predicate(labels: frozenset[str]) -> bool:
        return name in labels

    return predicate


def _compile_not(inner: Callable[[frozenset[str]], bool]) -> Callable[[frozenset[str]], bool]:
    def predicate(labels: frozenset[str]) -> bool:
        return not inner(labels)

    return predicate


def _compile_and(
    lp: Callable[[frozenset[str]], bool],
    rp: Callable[[frozenset[str]], bool],
) -> Callable[[frozenset[str]], bool]:
    def predicate(labels: frozenset[str]) -> bool:
        return lp(labels) and rp(labels)

    return predicate


def _compile_or(
    lp: Callable[[frozenset[str]], bool],
    rp: Callable[[frozenset[str]], bool],
) -> Callable[[frozenset[str]], bool]:
    def predicate(labels: frozenset[str]) -> bool:
        return lp(labels) or rp(labels)

    return predicate


def compile(expr: LabelExpr) -> Callable[[frozenset[str]], bool]:  # noqa: A001 — compile is the canonical AST→predicate verb; builtin compile() is rarely used in domain code
    """Walk the AST once, producing a predicate over label sets."""
    match expr:
        case Label(name):
            return _compile_label(name)
        case Not(operand):
            return _compile_not(compile(operand))
        case And(left, right):
            return _compile_and(compile(left), compile(right))
        case Or(left, right):
            return _compile_or(compile(left), compile(right))


def parse_predicate(text: str) -> Callable[[frozenset[str]], bool]:
    """Parse + compile in one shot."""
    return compile(parse(text))
