"""Mail-merge build for the hoplite plugin.

Reads templates/build/manifest.txt, expands every ``{{<rel-path>}}`` marker in each
listed src by inlining the file at ``templates/<rel-path>``, and writes the result to
the corresponding dst. Composition is one level deep: a marker inside an inlined
component is an error.

Run from the repo root: ``python templates/build/build.py``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_ROOT = REPO_ROOT / "templates"
MANIFEST = TEMPLATES_ROOT / "build" / "manifest.txt"

_MARKER = re.compile(r"\{\{([^{}\n]+?)\}\}")


def _read_manifest() -> list[tuple[Path, Path]]:
    entries: list[tuple[Path, Path]] = []
    for lineno, raw in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "->" not in line:
            raise SystemExit(f"{MANIFEST}:{lineno}: expected '<src> -> <dst>'")
        src_str, dst_str = (part.strip() for part in line.split("->", 1))
        entries.append((REPO_ROOT / src_str, REPO_ROOT / dst_str))
    return entries


def _load_component(rel_path: str) -> str:
    path = TEMPLATES_ROOT / rel_path
    if not path.is_file():
        raise SystemExit(f"component not found: templates/{rel_path}")
    text = path.read_text(encoding="utf-8")
    if _MARKER.search(text):
        raise SystemExit(
            f"templates/{rel_path}: components must not contain {{{{...}}}} markers "
            "(composition is one level deep)"
        )
    return text


def _expand(src: Path) -> str:
    text = src.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        return _load_component(match.group(1).strip())

    return _MARKER.sub(replace, text)


def main() -> int:
    entries = _read_manifest()
    for src, dst in entries:
        if not src.is_file():
            raise SystemExit(f"src missing: {src.relative_to(REPO_ROOT)}")
        rendered = _expand(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(rendered, encoding="utf-8")
        rel_src = src.relative_to(REPO_ROOT).as_posix()
        rel_dst = dst.relative_to(REPO_ROOT).as_posix()
        print(f"  {rel_src} -> {rel_dst}")
    print(f"built {len(entries)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
