#!/usr/bin/env bash
# Write a wiki-style note to docs/notes/<slug>.md.
#
# Head fields are positional args. The body (## Observation, ## Interpretation,
# ## Next — or whatever sections the topic demands) is read from stdin and
# appended verbatim. The skill documents the body shape; this script does not
# validate it.
#
# Tags are free-form, comma-separated, may be empty (pass "").
#
# Output discipline:
#   - Success: silent. The file at docs/notes/<slug>.md is the artifact.
#   - Failure: validation error to stderr, non-zero exit.
#
# Usage:
#   record-note.sh [--force] <title> <tags> <summary> < body.md
#
# Examples:
#   record-note.sh "Cache TTL is 300s" 'auth-investigation,cache' \
#       'Confirmed via appsettings.json; the stale read was a cold-start artifact, not a TTL bug.' \
#       < body.md

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

FORCE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --force)
            FORCE=1
            shift ;;
        --)
            shift
            break ;;
        --*)
            echo "record-note.sh: unknown flag '$1'" >&2
            exit 2 ;;
        *)
            break ;;
    esac
done

TITLE="${1:-}"
TAGS="${2-}"
SUMMARY="${3:-}"

if [ -z "$TITLE" ] || [ -z "$SUMMARY" ]; then
    echo "usage: record-note.sh [--force] <title> <tags> <summary>  (body on stdin)" >&2
    exit 2
fi

if [ -t 0 ]; then
    echo "record-note.sh: body must be piped on stdin" >&2
    exit 2
fi

slug=$(printf '%s' "$TITLE" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g' \
    | sed -E 's/^-+|-+$//g' \
    | cut -c1-80)

if [ -z "$slug" ]; then
    echo "record-note.sh: title slug is empty after sanitization" >&2
    exit 2
fi

mkdir -p docs/notes
target="docs/notes/${slug}.md"

if [ -e "$target" ] && [ "$FORCE" != "1" ]; then
    echo "record-note.sh: $target already exists (use --force to overwrite)" >&2
    exit 2
fi

body=$(cat)

{
    printf '# %s\n\n' "$TITLE"
    printf 'Tags: %s\n' "$TAGS"
    printf '%s\n\n' "$SUMMARY"
    printf '%s\n' "$body"
} > "$target"
