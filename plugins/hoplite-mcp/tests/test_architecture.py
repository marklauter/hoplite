"""The layering contract and the package facade, asserted as tests.

`import-linter` reads its contracts from `pyproject.toml`, so the dependency direction is
configured once beside the ruff and pyright settings. Running it here rather than as a
separate gate step means a violation fails the same command everything else fails.
"""

from __future__ import annotations

from pathlib import Path

from importlinter import configuration
from importlinter.application import use_cases

import hoplite_catalog
from hoplite_catalog import adapters, contents, ports, vocabulary

# Registers the built-in contract types. The CLI and the `api` module both do this on the
# way in; calling `use_cases` directly skips it, and the run fails on a missing registry
# rather than on a violated contract.
configuration.configure()

_PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_the_package_layers_in_one_direction() -> None:
    # cache_dir=None keeps the run from leaving a cache directory in the working tree.
    assert use_cases.lint_imports(config_filename=str(_PYPROJECT), cache_dir=None)


def test_the_package_re_exports_every_public_name() -> None:
    # The facade went stale twice: `UnlistableDirectory` was added to `contents` and not
    # here, and `files` was added whole. A name a module exports and the package does not
    # is an import that works one way and fails the other, for no stated reason.
    modules = (
        set(contents.__all__) | set(ports.__all__) | set(adapters.__all__) | set(vocabulary.__all__)
    )
    assert set(hoplite_catalog.__all__) == modules


def test_the_facade_does_not_pull_in_the_host() -> None:
    # `server` binds stdin and stdout and is an entry point. Importing the library must not
    # reach it, which is also what the layering contract says from the other direction.
    assert "server" not in hoplite_catalog.__all__
