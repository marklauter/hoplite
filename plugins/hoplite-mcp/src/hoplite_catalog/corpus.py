"""The corpus: a filesystem, the root inside it, and the questions asked of both.

Every walking function used to take ``(files, root)`` and re-derive the resolved root from
it — six call sites did their own ``files.resolve(root)``, and ``corpus_path`` did one more
for every path the report emits. The two arguments are one thing, so they are one type. The
root is resolved once, at construction, and after that "the root is resolved" is true by
construction rather than restated wherever containment is checked.

The port is not exposed. ``Corpus`` forwards the seven questions the walk asks of a
filesystem, so the core never names ``Files`` and there is one way to reach a filesystem
from it. What gets injected is still a ``Files``; what the core holds is a corpus.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import final

from hoplite_catalog.ports import Files

__all__ = ["Corpus"]


@final
@dataclass(frozen=True, slots=True)
class Corpus:
    """A rooted, readable corpus. ``root`` is resolved; every method may raise ``OSError``.

    ``_files`` is the injected port and not part of the contract: the delegating methods
    below are, so a caller cannot reach the filesystem two ways.
    """

    _files: Files
    root: Path

    def __post_init__(self) -> None:
        # The one resolve. `object.__setattr__` is how a frozen dataclass normalizes in
        # `__post_init__`; the alternative is a classmethod constructor, which leaves the
        # plain one able to build a corpus whose root is not resolved.
        object.__setattr__(self, "root", self._files.resolve(self.root))

    def entries(self, directory: Path) -> tuple[Path, ...]:
        return self._files.entries(directory)

    def is_directory(self, path: Path) -> bool:
        return self._files.is_directory(path)

    def is_file(self, path: Path) -> bool:
        return self._files.is_file(path)

    def is_symlink(self, path: Path) -> bool:
        return self._files.is_symlink(path)

    def exists(self, path: Path) -> bool:
        return self._files.exists(path)

    def resolve(self, path: Path) -> Path:
        return self._files.resolve(path)

    def read_text(self, path: Path) -> str:
        return self._files.read_text(path)

    def contains(self, path: Path) -> bool:
        """True when ``path`` is the root or sits beneath it. Lexical: no link is followed.

        This is the question asked of a path the caller supplied, where ``..`` traversal is
        what it stops.
        """
        return path == self.root or self.root in path.parents

    def contains_target(self, path: Path) -> bool:
        """True when what ``path`` points at is the root or sits beneath it.

        The question asked before reading or emitting a path, because reads follow links:
        ``docs/external -> /somewhere/else`` is lexically inside and resolves outside, and
        reporting it under ``docs/`` is a listing that lies about what the corpus contains.
        Following a link is itself I/O, so this raises what ``resolve`` raises.
        """
        return self.contains(self.resolve(path))

    def path_of(self, path: Path) -> str:
        """``path`` as the corpus addresses it — root-relative, forward slashes.

        ``path`` is deliberately not resolved: ``docs/specs/frontmatter.md`` is a symlink
        into ``plugins/hoplite-skills/references/``, and resolving it would report a path no
        wikilink in the corpus uses. A path is a link address; where the bytes live is not
        this type's business.
        """
        return path.absolute().relative_to(self.root).as_posix()
