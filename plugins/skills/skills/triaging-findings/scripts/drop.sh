#!/usr/bin/env bash
# Delete a finding after triage decided Drop or after a Fix landed.
#
# The slug is the finding's basename without the .md suffix — the same
# slug printed by list-findings.sh under "→ <slug>.md". The script
# resolves the finding under <git-toplevel>/.findings/ (or .findings/
# relative to CWD when outside a git repo) so it stays consistent with
# the reviewer scripts.
#
# Output discipline:
#   - Success: silent. The finding is gone; the proposal document is the
#              audit trail.
#   - Failure: error to stderr, non-zero exit. The finding is preserved.
#
# Usage:
#   drop.sh <slug>
#
# Example:
#   drop.sh domain-throws-on-missing-order

set -eo pipefail

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/../../../scripts/_lib.sh"

SLUG="${1:-}"

if [ -z "$SLUG" ]; then
    echo "usage: drop.sh <slug>" >&2
    exit 2
fi

# Reject paths to keep the script slug-shaped — refuse anything with a
# path separator or a `.md` suffix, since both indicate the caller passed
# the wrong thing.
case "$SLUG" in
    */*|*\\*)
        echo "drop.sh: slug must not contain a path separator, got '$SLUG'" >&2
        exit 2
        ;;
    *.md)
        echo "drop.sh: slug must not include the .md suffix, got '$SLUG'" >&2
        exit 2
        ;;
esac

dir=$(findings_dir)
target="${dir}/${SLUG}.md"

if [ ! -f "$target" ]; then
    echo "drop.sh: finding not found: $target" >&2
    exit 2
fi

rm "$target"
