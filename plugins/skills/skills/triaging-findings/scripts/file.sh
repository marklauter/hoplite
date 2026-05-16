#!/usr/bin/env bash
# File a finding as a GitHub issue and delete the finding on success.
#
# The issue body is read from stdin — the agent reshapes the finding's
# Observation / Why-it-matters / Suggested-fix sections into the template's
# required fields during proposal authoring, then pipes the composed body
# here. The title comes from the finding's H1.
#
# The script is a thin bridge: it does not transform the body. It locates
# the finding under <git-toplevel>/.findings/, reads its title, hands the
# body off to managing-github-issues/create.sh with the given template,
# and removes the finding when create.sh exits zero. The finding stays on
# disk when filing fails so the steward can retry.
#
# Labels declared on the template apply automatically through create.sh.
# Extra labels pass via the LABELS env var (comma-separated).
#
# Output discipline:
#   - Success: the created issue's URL (gh's output via create.sh).
#   - Failure: the underlying error, exit with that command's code. The
#              finding is preserved on failure.
#
# Usage:
#   cat composed-body.md | file.sh <slug> <template-name>
#   LABELS="priority:high,area:serialization" file.sh <slug> tech-debt.yml < body.md

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/../../../scripts/_lib.sh"

SLUG="${1:-}"
TEMPLATE="${2:-}"

if [ -z "$SLUG" ] || [ -z "$TEMPLATE" ]; then
    echo "usage: file.sh <slug> <template-name>  (body on stdin)" >&2
    exit 2
fi

case "$SLUG" in
    */*|*\\*)
        echo "file.sh: slug must not contain a path separator, got '$SLUG'" >&2
        exit 2
        ;;
    *.md)
        echo "file.sh: slug must not include the .md suffix, got '$SLUG'" >&2
        exit 2
        ;;
esac

if [ -t 0 ]; then
    echo "file.sh: body must be piped on stdin" >&2
    exit 2
fi

dir=$(findings_dir)
finding="${dir}/${SLUG}.md"

if [ ! -f "$finding" ]; then
    echo "file.sh: finding not found: $finding" >&2
    exit 2
fi

title=$(sed -n '1s/^# //p' "$finding")
if [ -z "$title" ]; then
    echo "file.sh: finding has no H1 title: $finding" >&2
    exit 2
fi

# Locate create.sh in the sibling skill. The path is stable across the
# plugin tree; PLUGIN_ROOT is honored when set so tests can stub.
plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
create="${plugin_root}/skills/managing-github-issues/scripts/create.sh"

if [ ! -x "$create" ] && [ ! -f "$create" ]; then
    echo "file.sh: create.sh not found at $create" >&2
    exit 2
fi

# Pipe the composed body straight through. LABELS env var passes through
# automatically because it is read by create.sh from its own environment.
# Capture exit code explicitly so `set -e` does not abort before cleanup.
rc=0
bash "$create" "$TEMPLATE" "$title" || rc=$?

if [ "$rc" -eq 0 ]; then
    rm "$finding"
fi

exit "$rc"
