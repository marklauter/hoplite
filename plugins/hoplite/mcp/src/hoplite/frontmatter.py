"""Frontmatter parsing for the Hoplite corpus.

Splits the leading YAML frontmatter block, validates the mandatory fields, and
classifies keys per the class-prefix contract (see
``templates/components/shape/frontmatter.md``):

- ``title`` / ``summary`` — bare first-class fields, FTS-indexed, not properties.
- ``document.<key>`` — node properties; the prefix is stripped on store and
  ``tags`` values are casefolded.
- ``edge.<stereotype>`` — edge stereotypes (lists of target paths), consumed by
  the walker to emit ``mentions`` edges plus ``edge_property`` rows.

Both the flat dotted form and the nested mapping form are accepted and normalized
to the same dotted keys::

    # flat
    document.tags: [note]
    edge.blocked_by: [docs/notes/foo.md]

    # nested (equivalent)
    document:
      tags: [note]
    edge:
      blocked_by: [docs/notes/foo.md]
"""

from __future__ import annotations

import re
from typing import Any, Final, cast

import yaml

__all__ = [
    "FRONTMATTER_RE",
    "MANDATORY_FIELDS",
    "edge_stereotypes",
    "fts_fields",
    "parse",
    "to_properties",
]

# Matches `---\n...\n---\n` at the start of the file. `\r?\n` covers LF and CRLF
# (Obsidian on Windows writes CRLF).
FRONTMATTER_RE: Final = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)

# Mandatory keys in authored form: title/summary bare, tags/created document.-prefixed.
# aliases is optional.
MANDATORY_FIELDS: Final = ("title", "summary", "document.tags", "document.created")

_DOCUMENT_PREFIX: Final = "document."
_EDGE_PREFIX: Final = "edge."
# Top-level keys whose mapping value expands into dotted keys (the nested form).
_NESTED_CLASSES: Final = ("document", "edge")


def parse(
    canonical: str,
    text: str,
    warnings: list[str],
) -> tuple[dict[str, Any] | None, str]:
    """Split frontmatter from body and parse it; return ``(meta, body)`` or ``(None, "")``.

    ``meta`` is normalized: nested ``document:`` / ``edge:`` mappings are flattened
    into dotted keys, so callers always see ``document.<key>`` / ``edge.<key>``
    regardless of the authored shape. Validates the mandatory fields and that
    ``document.tags`` (and ``document.aliases`` when present) are lists.
    """
    match = FRONTMATTER_RE.match(text)
    if match is None:
        warnings.append(f"{canonical}: missing or unterminated frontmatter")
        return None, ""
    body = text[match.end() :]
    try:
        raw_meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        warnings.append(f"{canonical}: yaml parse error: {exc}")
        return None, ""
    if raw_meta is None:
        raw_meta = {}
    if not isinstance(raw_meta, dict):
        warnings.append(f"{canonical}: frontmatter is not a mapping")
        return None, ""

    meta = _normalize(cast("dict[object, object]", raw_meta))

    missing = [field for field in MANDATORY_FIELDS if field not in meta]
    if missing:
        warnings.append(f"{canonical}: missing mandatory fields: {missing}")
        return None, ""
    if not isinstance(meta["document.tags"], list):
        warnings.append(f"{canonical}: document.tags must be a list")
        return None, ""
    if "document.aliases" in meta and not isinstance(meta["document.aliases"], list):
        warnings.append(f"{canonical}: document.aliases must be a list")
        return None, ""
    return meta, body


def _normalize(raw: dict[object, object]) -> dict[str, Any]:
    """Flatten nested ``document:`` / ``edge:`` mappings into dotted keys.

    Accepts both the flat dotted form (``document.tags``) and the nested mapping
    form, normalizing both to dotted keys. When a key arrives in both shapes,
    list values are merged and scalars keep the first value seen.
    """
    flat: dict[str, Any] = {}

    def put(key: str, value: Any) -> None:
        if key in flat and isinstance(flat[key], list) and isinstance(value, list):
            flat[key] = [*flat[key], *value]
        else:
            flat.setdefault(key, value)

    for raw_key, value in raw.items():
        key = str(raw_key)
        if key in _NESTED_CLASSES and isinstance(value, dict):
            for sub, subval in cast("dict[object, object]", value).items():
                put(f"{key}.{sub}", subval)
        else:
            put(key, value)
    return flat


def fts_fields(meta: dict[str, Any]) -> tuple[str, str]:
    """Return ``(title, summary)`` — the bare first-class FTS fields."""
    return str(meta.get("title", "")), str(meta.get("summary", ""))


def to_properties(meta: dict[str, Any]) -> dict[str, list[str]]:
    """Project ``document.<key>`` entries into the EAV node-property shape.

    The ``document.`` prefix is stripped. Scalars become single-element lists;
    lists become one entry per element (empty lists produce no entry). ``tags``
    values are casefolded so predicate lookups match case-insensitively; other
    values are stored verbatim. Bare ``title``/``summary`` (FTS fields) and
    ``edge.<...>`` keys (edge stereotypes) are excluded.
    """
    props: dict[str, list[str]] = {}
    for key, value in meta.items():
        if not key.startswith(_DOCUMENT_PREFIX):
            continue
        prop_key = key[len(_DOCUMENT_PREFIX) :]
        if isinstance(value, list):
            items = cast("list[object]", value)
            if not items:
                continue
            if prop_key == "tags":
                props[prop_key] = [str(item).casefold() for item in items]
            else:
                props[prop_key] = [str(item) for item in items]
        elif value is None:
            continue
        else:
            props[prop_key] = [str(value)]
    return props


def edge_stereotypes(meta: dict[str, Any]) -> dict[str, list[str]]:
    """Extract ``edge.<stereotype>: [paths]`` entries as ``{stereotype: [paths]}``.

    The walker turns each path into a ``mentions`` edge plus an ``edge_property``
    stereotype row. Non-list edge values are ignored — the stereotype contract is
    a list of target paths.
    """
    result: dict[str, list[str]] = {}
    for key, value in meta.items():
        if not key.startswith(_EDGE_PREFIX):
            continue
        stereotype = key[len(_EDGE_PREFIX) :]
        if isinstance(value, list):
            paths = [str(item) for item in cast("list[object]", value) if item is not None]
            if paths:
                result[stereotype] = paths
    return result
