"""The Hoplite `catalog` MCP server.

Two tools today: ``contents``, a per-directory frontmatter listing over the corpus, and
``vocabulary``, a count of the frontmatter keys in use. The graph tools designed in
``docs/specs/hoplite-tool-api.md`` are not built yet.

``Files`` is the filesystem port and ``RealFiles`` is the only adapter shipped. ``Corpus``
pairs a port with a resolved root and is what every walking function takes as its first
argument. ``server`` is not re-exported here: it is the composition root and an entry
point, so importing this package must not pull the host in.

What is re-exported is the whole of it: build a corpus, address a path in it, ask it the
two questions, read the records that come back, and render them. It is smaller than the
sum of what the modules export, deliberately. ``slice_frontmatter``, ``group_properties``,
``read_entry``, ``markdown_in``, ``subdirectories``, and ``FENCE`` are part of their own
module's contract and stay reachable there — the tests drive them directly, because a
line scanner is the cheapest thing in the suite to test and routing it through ``collect``
would make every failure less local.

They are not part of this package's contract, because each is a step inside one that is:
``markdown_in`` is one branch of ``collect``, ``read_entry`` is its loop body,
``subdirectories`` is a slice of the walk's partition, and the scanners are what an
``Entry`` is built from. Re-exporting them offers a second way to do what ``collect``
already does, with none of the guards it wraps them in — the containment check at the read,
the reason reported in place of a document that could not be opened, the de-duplication of
one document reached by two paths. Every name here is a promise that narrowing again would
break, so the ones that buy a caller nothing are not made.
"""

import sys

# The first thing the package does, because everything below it is what would fail first.
# `contents` and `documents` use PEP 695 `type` statements, which do not parse before 3.12,
# so an older interpreter dies with a SyntaxError pointing at a type alias — a true report
# of a symptom and no help at all with the cause. `python -m hoplite_catalog.server` imports
# this module before that one, and nothing here uses syntax newer than the check itself, so
# this is the last point where a sentence can still be printed.
#
# `SystemExit` rather than `ImportError`: one line on stderr and an exit code, where a
# traceback buries the sentence under a stack nobody needs. The cost is that importing the
# package would stop any process, not just this one — moot on every interpreter that can
# parse the rest of it.
# UP036 is suppressed below: ruff reads this as a dead version block because
# `target-version` is py312. It is dead for every version this project targets, and live for
# the one it does not — the check exists to run on an interpreter the configuration says will
# never reach it.
if sys.version_info < (3, 12):  # noqa: UP036
    raise SystemExit(
        f"hoplite-catalog needs Python 3.12 or newer; {sys.executable} is "
        f"{sys.version.split()[0]}. Set the plugin's Python executable option to a 3.12+ one."
    )

from hoplite_catalog.adapters import RealFiles
from hoplite_catalog.contents import (
    Directory,
    DirectoryNode,
    File,
    FileNode,
    ForeignDirectory,
    ForeignFile,
    Report,
    UnlistableDirectory,
    UnreadableFile,
    collect,
    other_files,
    resolve_under,
    survey,
    walk,
)
from hoplite_catalog.corpus import Corpus, ResolvedRoot
from hoplite_catalog.documents import Document, Entry, Property, Unreadable
from hoplite_catalog.ports import Files
from hoplite_catalog.refusals import (
    Missing,
    NoSuchKeys,
    NotAList,
    NotAString,
    NotMarkdown,
    OutsideRoot,
    Refusal,
    ResolvesOutside,
    Unaddressable,
    UnknownTool,
)
from hoplite_catalog.rendering import render, render_refusal, render_report, render_vocabulary
from hoplite_catalog.vocabulary import KeyUse, tally

__all__ = [
    "Corpus",
    "Directory",
    "DirectoryNode",
    "Document",
    "Entry",
    "File",
    "FileNode",
    "Files",
    "ForeignDirectory",
    "ForeignFile",
    "KeyUse",
    "Missing",
    "NoSuchKeys",
    "NotAList",
    "NotAString",
    "NotMarkdown",
    "OutsideRoot",
    "Property",
    "RealFiles",
    "Refusal",
    "Report",
    "ResolvedRoot",
    "ResolvesOutside",
    "Unaddressable",
    "UnknownTool",
    "UnlistableDirectory",
    "Unreadable",
    "UnreadableFile",
    "collect",
    "other_files",
    "render",
    "render_refusal",
    "render_report",
    "render_vocabulary",
    "resolve_under",
    "survey",
    "tally",
    "walk",
]
