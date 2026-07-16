---
title: os.execv to subprocess.run
summary: First-cut launch.py replaced its own process with the venv'd Python via os.execv; the MCP supervisor's child-PID assumptions broke. subprocess.run with launch.py as a parent that waits for the child is the cleaner shape.
tags: [journal, mcp, bootstrap, python, decision]
created: 2026-05-25
---

# os.execv to subprocess.run

First-cut `launch.py` replaced its own process with the venv'd Python via `os.execv`; the MCP supervisor's child-PID assumptions broke. `subprocess.run` with `launch.py` as a parent that waits for the child is the cleaner shape.

## What execv was for

The plugin manifest registers a command for the MCP server. The supervisor invokes that command and treats the resulting process as the MCP server: it reads from the child's stdout, writes to its stdin, watches its exit code. `launch.py` is the registered command. Its job is to dispatch to the venv'd Python that has the `hoplite` package installed.

The first-cut shape used `os.execv`:

```python
os.execv(venv_python, [venv_python, "-m", "hoplite"])
```

`execv` replaces the current process image with the new program. Same PID, same parent, same stdio handles. From the supervisor's vantage, no fork happened — the child it spawned is still the same child, just running different code now.

In principle, this is the cleanest shape: one process, no overhead from a parent waiting on a child.

## Why it broke

The MCP supervisor watches the child PID for liveness. The supervisor tracks the process group it spawned and assumes the binary it invoked is the binary it gets back. When `execv` replaced `launch.py` with the venv'd Python, the child PID was still the original, but several things changed:

- The executable name in `/proc/<pid>/comm` (Linux) or its equivalent on macOS and Windows became the venv'd Python instead of `launch.py`. Supervisor logs and monitoring saw an unexpected binary.
- Signal handlers installed by `launch.py` retired silently. Any teardown hook that `launch.py` had registered was gone after the exec.
- Stdio redirection through `launch.py` was no longer available. If `launch.py` had wanted to log incoming traffic before forwarding, the exec made that impossible.

On Windows specifically, `os.execv` does not have the same semantics as on Unix — it spawns a new process and exits the current one, but the parent (the supervisor) sees this as the child exiting. The supervisor concluded the MCP server had crashed.

## The fix

Replace `execv` with `subprocess.run`:

```python
result = subprocess.run(
    [venv_python, "-m", "hoplite"],
    check=False,
)
sys.exit(result.returncode)
```

`launch.py` becomes a parent that spawns the venv'd Python as a child, waits for it, and exits with the child's return code. The supervisor sees `launch.py` as the live process throughout the session; the venv'd Python is a child of `launch.py`, transparent to the supervisor.

The overhead: one extra Python process holding open during the session. ~5 MB of memory and zero CPU after startup. Negligible.

## Decisions captured

- Supervisor expectations are not negotiable. The MCP supervisor was built against a particular process model. Trying to fit a different shape (exec-replacement) into that model fails on multiple OSes for OS-specific reasons.
- `subprocess.run` over `os.execv` when a supervisor is watching. The extra process is cheap; the matched-shape benefit is real.
- Windows is the constraint. Even if `execv` worked cleanly on Linux and macOS, Windows would still break. Cross-platform support means the lowest-common-denominator shape; `subprocess.run` is that shape.

## What this is part of

The venv-bootstrap arc — see [[docs/journal/2026-05-25-0413-venv-bootstrap-race.md]] for the broader cycle this fix lived inside. The execv defect surfaced minutes after the SessionStart bootstrap landed; the fix went in at 03:38, the bigger race-defense at 03:42, the pip-failure-teardown at 04:13.

## Cross-references

- `[[journal/2026-05-25-0413-venv-bootstrap-race]]` — the broader bootstrap milestone.
