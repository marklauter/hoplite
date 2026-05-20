#!/usr/bin/env bash
# Write an engineering-notebook-style journal entry to docs/journal/YYYY-MM-DD-HHMM-<slug>.md.
#
# Head fields are positional args. The body (## Context, ## Attempted,
# ## Outcome, ## Decision, ## Next — or whatever sections the cycle demands)
# is read from stdin and appended verbatim. The skill documents the body
# shape; this script does not validate it.
#
# Tags are free-form, comma-separated, may be empty (pass "").
#
# Append-only by design: no --force flag. The script refuses to overwrite an
# existing file. Corrections are new entries that reference the old.
#
# Output discipline:
#   - Success: silent. The file at docs/journal/<filename>.md is the artifact.
#   - Failure: validation error to stderr, non-zero exit.
#
# Usage:
#   record-entry.sh <title> <tags> <summary> < body.md
#
# Example:
#   record-entry.sh "Verified cache TTL via config" 'auth-investigation,cache' \
#       'Confirmed the 300s TTL in appsettings.json; closes the stale-read thread.' \
#       < body.md

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

TITLE="${1:-}"
TAGS="${2-}"
SUMMARY="${3:-}"

if [ -z "$TITLE" ] || [ -z "$SUMMARY" ]; then
    echo "usage: record-entry.sh <title> <tags> <summary>  (body on stdin)" >&2
    exit 2
fi

if [ -t 0 ]; then
    echo "record-entry.sh: body must be piped on stdin" >&2
    exit 2
fi

date_part=$(date +%Y-%m-%d)
time_part=$(date +%H%M)
date_head="${date_part} $(date +%H:%M)"

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
slug=$(bash "$plugin_root/scripts/slugify.sh" "$TITLE")

if [ -z "$slug" ]; then
    echo "record-entry.sh: title slug is empty after sanitization" >&2
    exit 2
fi

mkdir -p docs/journal
target="docs/journal/${date_part}-${time_part}-${slug}.md"

if [ -e "$target" ]; then
    echo "record-entry.sh: $target already exists (journal is append-only; choose a more specific title or wait one minute)" >&2
    exit 2
fi

body=$(cat)

{
    printf '# %s\n\n' "$TITLE"
    printf 'date: %s\n' "$date_head"
    printf 'tags: %s\n' "$TAGS"
    printf '%s\n\n' "$SUMMARY"
    printf '%s\n' "$body"
} > "$target"
