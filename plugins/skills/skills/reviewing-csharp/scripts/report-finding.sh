#!/usr/bin/env bash
# Write a review finding to .findings/<slug>.md.
#
# Head fields are positional args. The body (## Observation, ## Why it matters,
# ## Suggested fix) is read from stdin and appended verbatim. The skill
# documents the body shape; this script does not validate it.
#
# Severity must be one of: important, nit, pre-existing.
# Location may be a single `path:line` or a comma-separated list.
# Principle is free-form; the writing-csharp Philosophy heading is preferred.
#
# Output discipline:
#   - Success: silent. The file at .findings/<slug>.md is the artifact.
#   - Failure: validation error to stderr, non-zero exit.
#
# Usage:
#   report-finding.sh [--force] <title> <severity> <location> <principle> <summary> < body.md
#
# Examples:
#   report-finding.sh "Domain layer throws on missing order" important \
#       'src/Domain/Orders/OrderService.cs:84' \
#       'Results, not exceptions' \
#       'Throws InvalidOperationException for a domain failure that should be Result.NotFound.' \
#       < body.md

set -e

FORCE=0
if [ "${1:-}" = "--force" ]; then
    FORCE=1
    shift
fi

TITLE="${1:-}"
SEVERITY="${2:-}"
LOCATION="${3:-}"
PRINCIPLE="${4:-}"
SUMMARY="${5:-}"

if [ -z "$TITLE" ] || [ -z "$SEVERITY" ] || [ -z "$LOCATION" ] || [ -z "$PRINCIPLE" ] || [ -z "$SUMMARY" ]; then
    echo "usage: report-finding.sh [--force] <title> <severity> <location> <principle> <summary>  (body on stdin)" >&2
    exit 2
fi

case "$SEVERITY" in
    important|nit|pre-existing) ;;
    *)
        echo "report-finding.sh: invalid severity '$SEVERITY' (must be important, nit, or pre-existing)" >&2
        exit 2
        ;;
esac

if [ -t 0 ]; then
    echo "report-finding.sh: body must be piped on stdin" >&2
    exit 2
fi

slug=$(printf '%s' "$TITLE" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g' \
    | sed -E 's/^-+|-+$//g' \
    | cut -c1-80)

if [ -z "$slug" ]; then
    echo "report-finding.sh: title slug is empty after sanitization" >&2
    exit 2
fi

mkdir -p .findings
target=".findings/${slug}.md"

if [ -e "$target" ] && [ "$FORCE" != "1" ]; then
    echo "report-finding.sh: $target already exists (use --force to overwrite)" >&2
    exit 2
fi

body=$(cat)

{
    printf '# %s\n\n' "$TITLE"
    printf 'Severity: %s\n' "$SEVERITY"
    printf 'Location: `%s`\n' "$LOCATION"
    printf 'Principle: %s\n' "$PRINCIPLE"
    printf '%s\n\n' "$SUMMARY"
    printf '%s\n' "$body"
} > "$target"
