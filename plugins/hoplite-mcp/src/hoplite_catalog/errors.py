"""The one exception the host turns into an answer.

``_call_tool`` used to catch ``ValueError``, which is what ``resolve_under`` and the
argument readers raise — and also what a bug raises. A misspelled ``under`` and a defect in
the walk came back as the same thing: a polite tool-error result the agent reads and
retries against, with nothing written to the log. Naming the caller's half of that channel
is what lets the other half fail loudly.

It lives here rather than in ``contents`` or ``server`` because both raise it and neither
owns it: three of the four sites are corpus addressing, the rest are argument shapes.
"""

from __future__ import annotations

__all__ = ["CallerError"]


class CallerError(ValueError):
    """The caller asked for something it could have gotten right.

    A folder that does not exist, a path outside the corpus root, an argument of the wrong
    shape. Per the error model in ``docs/specs/hoplite-tool-api.md`` these come back as an
    error result carrying the message, rather than as an empty listing — a silent empty
    result reads as "the folder is empty", not "you typo'd".

    A ``ValueError`` subclass, because that is what each of these would otherwise be and a
    caller catching the built-in still catches it. What changed is the other direction: a
    plain ``ValueError`` is now a bug, and the host reports it as one.
    """
