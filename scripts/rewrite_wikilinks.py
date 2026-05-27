"""One-shot: rewrite wikilinks across the repo to the new convention.

Real refs → `[[docs/<path>.md]]` (file exists on disk).
Open loops → `[[ghost/<slug>]]` (no matching file).

Code spans and fenced blocks are skipped (rule 1: samples wear backticks).
Alias and anchor parts of an existing wikilink are preserved.

Run from the repo root:  python scripts/rewrite_wikilinks.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_FENCE_RE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RE = re.compile(r"`+[^`\n]+?`+")


def _mask_code(body: str) -> str:
    def _spaces(m: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))

    body = _FENCE_RE.sub(_spaces, body)
    body = _INLINE_CODE_RE.sub(_spaces, body)
    return body


def _build_basename_index() -> dict[str, list[str]]:
    """Map basename (with and without .md) → list of repo-relative paths."""
    index: dict[str, list[str]] = {}
    for md in DOCS_ROOT.rglob("*.md"):
        rel = md.relative_to(REPO_ROOT).as_posix()
        stem = md.stem
        name = md.name
        index.setdefault(stem.casefold(), []).append(rel)
        index.setdefault(name.casefold(), []).append(rel)
    return index


def _path_exists(rel: str) -> bool:
    return (REPO_ROOT / rel).is_file()


def _classify(target: str, basename_index: dict[str, list[str]]) -> str:
    """Return the new target string (without [[ ]] wrapping)."""
    # Preserve alias and anchor; only the path part (before # and |) gets rewritten.
    path_part = target
    anchor = ""
    alias = ""
    if "|" in path_part:
        path_part, alias = path_part.split("|", 1)
        alias = "|" + alias
    if "#" in path_part:
        path_part, anchor = path_part.split("#", 1)
        anchor = "#" + anchor
    path_part = path_part.strip()
    if not path_part:
        return target  # malformed; leave alone

    if path_part.startswith("docs/"):
        new_path = path_part if path_part.endswith(".md") else path_part + ".md"
        return f"{new_path}{anchor}{alias}"

    if path_part.startswith("ghost/"):
        return f"{path_part}{anchor}{alias}"

    # Try as a corpus-relative path: e.g. `notes/foo`, `hoplite/architecture`, `journal/2026-...`.
    candidate_with_md = path_part if path_part.endswith(".md") else path_part + ".md"
    candidate_rel = f"docs/{candidate_with_md}"
    if _path_exists(candidate_rel):
        return f"{candidate_rel}{anchor}{alias}"

    # Try as a bare slug — match by stem/name across docs/.
    matches = basename_index.get(path_part.casefold())
    if matches and len(matches) == 1:
        rel = matches[0]
        return f"{rel}{anchor}{alias}"

    # No file matches — declare it an intentional ghost. Slug is the path-part minus .md.
    slug = path_part[:-3] if path_part.endswith(".md") else path_part
    return f"ghost/{slug}{anchor}{alias}"


def _rewrite_file(path: Path, basename_index: dict[str, list[str]]) -> int:
    text = path.read_text(encoding="utf-8")
    masked = _mask_code(text)
    edits: list[tuple[int, int, str]] = []
    for match in _WIKILINK_RE.finditer(masked):
        old_target = match.group(1).strip()
        if not old_target:
            continue
        new_target = _classify(old_target, basename_index)
        if new_target == match.group(1):
            continue
        edits.append((match.start(1), match.end(1), new_target))
    if not edits:
        return 0
    out_parts: list[str] = []
    cursor = 0
    for start, end, replacement in edits:
        out_parts.append(text[cursor:start])
        out_parts.append(replacement)
        cursor = end
    out_parts.append(text[cursor:])
    path.write_text("".join(out_parts), encoding="utf-8")
    return len(edits)


def main() -> int:
    basename_index = _build_basename_index()
    total_edits = 0
    files_touched = 0
    for md in REPO_ROOT.rglob("*.md"):
        rel = md.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(".hoplite/") or "/.hoplite/" in rel:
            continue
        if "/venv/" in rel or "/.git/" in rel:
            continue
        edits = _rewrite_file(md, basename_index)
        if edits:
            files_touched += 1
            total_edits += edits
            print(f"{rel}: {edits} wikilink(s) rewritten")
    print(f"\nTotal: {total_edits} wikilinks in {files_touched} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
