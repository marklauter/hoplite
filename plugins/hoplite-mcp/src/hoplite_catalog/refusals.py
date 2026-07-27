"""What the caller asked for, when it could have asked better.

A refusal is a value, not an exception. Rejecting an ``under`` is a parse rejecting its
input: the operation is total, the rejection is inside its codomain, and the host acts on
it by answering ``isError: true`` with the reason. So it is returned. What is left to
raise is what is outside the codomain — the substrate failing, or the code being wrong —
and the host reports those as ``-32603`` with a traceback on stderr. The two channels are
now different types rather than two subclasses of ``ValueError`` telling a typo apart from
a defect by which class was caught first.

The variants carry the facts and none of the wording. ``rendering`` turns each into the
sentence the agent reads, the way it does for every other string a caller sees; a
pre-rendered English message on the record would put caller-facing prose back in the walk.

They live here rather than in ``contents`` or ``server`` because both produce them and
neither owns them: four are corpus addressing, three are argument shapes, and one is the
keys guard that needs both.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

__all__ = [
    "Missing",
    "NoSuchKeys",
    "NotAList",
    "NotAString",
    "NotMarkdown",
    "OutsideRoot",
    "Refusal",
    "ResolvesOutside",
    "Unaddressable",
    "UnknownTool",
]


@final
@dataclass(frozen=True, slots=True)
class OutsideRoot:
    """``under`` escapes the corpus root lexically — a ``..`` that climbs out of it."""

    under: str


@final
@dataclass(frozen=True, slots=True)
class ResolvesOutside:
    """``under`` is inside the root and points out of it. Reads follow links, so a folder
    linked out of the corpus would be read and reported under a corpus path."""

    under: str


@final
@dataclass(frozen=True, slots=True)
class Missing:
    """``under`` names nothing. A silent empty listing would read as "the folder is
    empty" rather than "you typo'd", which is the whole reason this channel exists."""

    under: str


@final
@dataclass(frozen=True, slots=True)
class NotMarkdown:
    """``under`` names a file that is not a ``.md`` document.

    Naming a file is the one path into the listing that skips the suffix test, and without
    this any file opening with ``---`` would have that block emitted — a ``.env`` someone
    wrote YAML into, a lockfile, a certificate.
    """

    under: str


@final
@dataclass(frozen=True, slots=True)
class NotAString:
    """An argument the schema declares a string arrived as something else."""

    argument: str


@final
@dataclass(frozen=True, slots=True)
class NotAList:
    """An argument the schema declares a list of strings arrived as something else."""

    argument: str


@final
@dataclass(frozen=True, slots=True)
class UnknownTool:
    """``tools/call`` named a tool this server does not have.

    ``name`` is whatever arrived on the wire, which is not necessarily a string.
    """

    name: object


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NoSuchKeys:
    """``keys`` named nothing any document in the folder carries.

    It would otherwise return a bare path list, which reads as "these documents have no
    frontmatter" rather than "that key does not exist".

    ``in_use`` is what the folder does carry, because the caller's next move is a second
    call with a corrected ``keys`` and the answer was already read to decide this.
    Withholding it costs them a ``vocabulary`` round trip to learn what this call knows.

    Keyword-only: ``requested`` and ``in_use`` are both ``tuple[str, ...]``, so
    positionally a transposed pair type-checks and blames the wrong list.
    """

    under: str
    requested: tuple[str, ...]
    in_use: tuple[str, ...]


# What can go wrong with a path the caller supplied. `resolve_under` returns one of these
# in place of a target, and both tools hand it straight back.
type Unaddressable = OutsideRoot | ResolvesOutside | Missing | NotMarkdown

# Every way a call can be the caller's mistake. The host renders one of these as an error
# result; anything else that goes wrong is not the caller's and is not one of these.
type Refusal = Unaddressable | NotAString | NotAList | UnknownTool | NoSuchKeys
