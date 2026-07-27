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
from hoplite_catalog import (
    adapters,
    contents,
    corpus,
    documents,
    ports,
    refusals,
    rendering,
    vocabulary,
)

# Registers the built-in contract types. The CLI and the `api` module both do this on the
# way in; calling `use_cases` directly skips it, and the run fails on a missing registry
# rather than on a violated contract.
configuration.configure()

_PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_the_package_layers_in_one_direction() -> None:
    # cache_dir=None keeps the run from leaving a cache directory in the working tree.
    assert use_cases.lint_imports(config_filename=str(_PYPROJECT), cache_dir=None)


def _module_exports() -> set[str]:
    return (
        set(contents.__all__)
        | set(corpus.__all__)
        | set(documents.__all__)
        | set(refusals.__all__)
        | set(ports.__all__)
        | set(rendering.__all__)
        | set(adapters.__all__)
        | set(vocabulary.__all__)
    )


def test_the_facade_promises_nothing_a_module_has_stopped_exporting() -> None:
    # This used to assert equality, which made the facade the sum of every module's
    # exports: adding a helper to `contents` failed the suite until it was also committed
    # to as package API, and a public name is a commitment that narrowing again breaks.
    # The facade is chosen now — see the package docstring for what it leaves out — so what
    # is left to check is that nothing in it has gone stale underneath.
    assert set(hoplite_catalog.__all__) <= _module_exports()


def test_every_name_the_facade_promises_is_bound() -> None:
    # An `__all__` entry with no import behind it is an `ImportError` for whoever tries it,
    # and `from hoplite_catalog import *` fails outright.
    assert [name for name in hoplite_catalog.__all__ if not hasattr(hoplite_catalog, name)] == []


def test_the_facade_does_not_pull_in_the_host() -> None:
    # `server` binds stdin and stdout and is an entry point. Importing the library must not
    # reach it, which is also what the layering contract says from the other direction.
    assert "server" not in hoplite_catalog.__all__
