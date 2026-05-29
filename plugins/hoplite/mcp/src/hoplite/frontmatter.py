"""Frontmatter parsing for the Hoplite corpus.

The contract — the class-prefix rules (``document.`` / ``edge.``), the bare
``title`` / ``summary`` fields, the mandatory set, and the dotted-or-nested
forms — is designed in ``docs/hoplite/hoplite-frontmatter.md`` (the source of
truth); ``templates/components/shape/frontmatter.md`` is the sparse operational
handbook derived from it. This module implements the contract; it does not
restate it.

``parse`` splits the leading YAML block, normalizes nested ``document:`` /
``edge:`` mappings to dotted keys, and validates. Two failure classes: a missing
mandatory field or a non-list ``document.tags`` / ``document.aliases`` drops the
document (warn, return ``None``); a null list element or a non-list
``edge.<stereotype>`` is dropped while the document is kept (warn, continue). The
projectors over the normalized ``meta`` are pure — ``fts_fields`` (bare
title/summary), ``to_properties`` (``document.<key>`` → EAV rows, ``tags``
casefolded), and ``edge_stereotypes`` (``edge.<key>`` → target-path lists).
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

# Mandatory keys: title and summary, both bare first-class FTS fields. Everything in
# the property bag — document.created, tags, aliases, and any document.<key> — is
# optional; tags and aliases are omit-when-empty when included.
MANDATORY_FIELDS: Final = ("title", "summary")
# Optional list fields that follow the omit-when-empty rule (non-empty or absent).
_OPTIONAL_LISTS: Final = ("document.tags", "document.aliases")

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
    regardless of the authored shape. Missing mandatory fields (title, summary,
    ``document.created``) or a present-but-non-list ``document.tags`` /
    ``document.aliases`` return ``(None, "")`` — the document drops out. Softer
    issues warn but keep the document: null list elements are dropped, an empty
    ``document.tags`` / ``document.aliases`` is flagged (omit it instead), and a
    non-list ``edge.<stereotype>`` is ignored.
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
    # tags and aliases are optional, but a present non-list value is malformed
    # enough to drop the document — its identity or links can't be read.
    for field in _OPTIONAL_LISTS:
        if field in meta and not isinstance(meta[field], list):
            warnings.append(f"{canonical}: {field} must be a list")
            return None, ""

    # Soft sanitization — warn but keep the document. A malformed annotation
    # shouldn't cost the whole file the way a missing mandatory field does.
    # Drop null list elements (a dangling `-` parses as None and carries no value).
    for key, value in meta.items():
        if isinstance(value, list) and None in value:
            kept = [item for item in value if item is not None]
            warnings.append(f"{canonical}: {key}: dropped {len(value) - len(kept)} empty list element(s)")
            meta[key] = kept
    # tags and aliases are omit-when-empty: an empty list is noise, not content.
    for field in _OPTIONAL_LISTS:
        if field in meta and isinstance(meta[field], list) and not meta[field]:
            warnings.append(f"{canonical}: {field} is empty; omit the key instead")
    # An edge.<stereotype> must be a list of target paths. Warn and drop a
    # non-list rather than silently swallowing the author's intended edge.
    for key in [k for k in meta if k.startswith(_EDGE_PREFIX)]:
        if not isinstance(meta[key], list):
            warnings.append(f"{canonical}: {key}: edge stereotype must be a list of paths; ignored")
            del meta[key]
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

    Each path becomes a ``mentions`` edge plus an ``edge_property`` stereotype row.
    ``parse`` already warns on and drops non-list ``edge.*`` values, so the list
    guard here is defensive — by contract every value reaching this point is a list.
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
