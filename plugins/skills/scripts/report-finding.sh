#!/usr/bin/env bash
# Write a review finding to .findings/<slug>.md.
#
# Head fields are written by name, so the artifact can grow new fields
# without breaking the readers (list-findings.sh, query.sh, summarize.sh
# all parse by name).
#
# Required:
#   --type        code | documentation
#   <title>       used to slug the filename
#   <severity>    important | nit | pre-existing
#   <location>    `path:line` or comma-separated `path:line, other:line`
#   <principle>   writing-X Philosophy heading is preferred
#   <summary>     one line
#   <body>        piped on stdin (## Observation, ## Why it matters, ## Suggested fix)
#
# Required for --type documentation:
#   --lens        Structure | Line | Copy | Accuracy | Coherence | References
#
# Forbidden for --type code:
#   --lens (lens classification belongs to documentation review only)
#
# Output discipline:
#   - Success: silent. The file at .findings/<slug>.md is the artifact.
#   - Failure: validation error to stderr, non-zero exit.
#
# Usage:
#   report-finding.sh [--force] --type <code|documentation> [--lens <name>] \
#       <title> <severity> <location> <principle> <summary> < body.md
#
# Examples:
#   report-finding.sh --type code \
#       "Domain layer throws on missing order" important \
#       'src/Domain/Orders/OrderService.cs:84' \
#       'Results, not exceptions' \
#       'Throws InvalidOperationException for a domain failure that should be Result.NotFound.' \
#       < body.md
#
#   report-finding.sh --type documentation --lens Line \
#       "README opens with hedge words" nit \
#       'README.md:3' \
#       'Every word must earn its place' \
#       'Opening paragraph uses might, perhaps, and basically in two sentences.' \
#       < body.md

set -eo pipefail

FORCE=0
TYPE=""
LENS=""

while [ $# -gt 0 ]; do
    case "$1" in
        --force)
            FORCE=1
            shift
            ;;
        --type)
            [ $# -ge 2 ] || { echo "report-finding.sh: --type requires a value" >&2; exit 2; }
            TYPE="$2"
            shift 2
            ;;
        --lens)
            [ $# -ge 2 ] || { echo "report-finding.sh: --lens requires a value" >&2; exit 2; }
            LENS="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        --*)
            echo "report-finding.sh: unknown flag '$1'" >&2
            exit 2
            ;;
        *)
            break
            ;;
    esac
done

TITLE="${1:-}"
SEVERITY="${2:-}"
LOCATION="${3:-}"
PRINCIPLE="${4:-}"
SUMMARY="${5:-}"

if [ -z "$TYPE" ] || [ -z "$TITLE" ] || [ -z "$SEVERITY" ] || [ -z "$LOCATION" ] || [ -z "$PRINCIPLE" ] || [ -z "$SUMMARY" ]; then
    echo "usage: report-finding.sh [--force] --type <code|documentation> [--lens <name>] <title> <severity> <location> <principle> <summary>  (body on stdin)" >&2
    exit 2
fi

# Strip leading/trailing backticks if the caller wrapped the location — the
# script renders them on write. Authors may pass either form.
LOCATION="${LOCATION#\`}"
LOCATION="${LOCATION%\`}"

case "$TYPE" in
    code|documentation) ;;
    *)
        echo "report-finding.sh: invalid type '$TYPE' (must be code or documentation)" >&2
        exit 2
        ;;
esac

case "$SEVERITY" in
    important|nit|pre-existing) ;;
    *)
        echo "report-finding.sh: invalid severity '$SEVERITY' (must be important, nit, or pre-existing)" >&2
        exit 2
        ;;
esac

if [ "$TYPE" = "documentation" ]; then
    if [ -z "$LENS" ]; then
        echo "report-finding.sh: --lens is required when --type is documentation" >&2
        exit 2
    fi
    case "$LENS" in
        Structure|Line|Copy|Accuracy|Coherence|References) ;;
        *)
            echo "report-finding.sh: invalid lens '$LENS' (must be Structure, Line, Copy, Accuracy, Coherence, or References)" >&2
            exit 2
            ;;
    esac
else
    if [ -n "$LENS" ]; then
        echo "report-finding.sh: --lens applies to --type documentation only" >&2
        exit 2
    fi
fi

if [ -t 0 ]; then
    echo "report-finding.sh: body must be piped on stdin" >&2
    exit 2
fi

slug=$(printf '%s' "$TITLE" \
    | LC_ALL=C tr '[:upper:]' '[:lower:]' \
    | LC_ALL=C sed -E 's/[^a-z0-9]+/-/g' \
    | LC_ALL=C sed -E 's/^-+|-+$//g' \
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
    printf 'Type: %s\n' "$TYPE"
    if [ -n "$LENS" ]; then
        printf 'Lens: %s\n' "$LENS"
    fi
    printf 'Location: `%s`\n' "$LOCATION"
    printf 'Principle: %s\n' "$PRINCIPLE"
    printf '%s\n\n' "$SUMMARY"
    printf '%s\n' "$body"
} > "$target"
