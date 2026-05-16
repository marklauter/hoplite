#!/usr/bin/env bash
# Write a review finding to .findings/<slug>.md.
#
# Head fields are written by name, so the artifact can grow new fields
# without breaking the readers (list-findings.sh, query.sh, summarize.sh
# all parse by name).
#
# Required:
#   --type        code | documentation | wiki
#   <title>       used to slug the filename
#   <severity>    important | nit | pre-existing
#   <location>    `path:line` or comma-separated `path:line, other:line`
#   <principle>   writing-X Philosophy heading is preferred
#   <summary>     one line
#   <body>        piped on stdin (## Observation, ## Why it matters, ## Suggested fix)
#
# Required for --type documentation and --type wiki:
#   --lens        Structure | Line | Copy | Accuracy | Coherence | References
#
# Forbidden for --type code:
#   --lens (lens classification belongs to documentation and wiki review)
#
# Output discipline:
#   - Success: silent. The file at .findings/<slug>.md is the artifact.
#   - Failure: validation error to stderr, non-zero exit.
#
# Slug collision: when .findings/<slug>.md already exists, the new finding
# is written to .findings/<slug>-2.md (or -3, -4, ... as needed). Writes
# always succeed; triage handles dedup. Audit runs can re-find the same
# defect across passes without losing prior findings.
#
# Usage:
#   report-finding.sh --type <code|documentation|wiki> [--lens <name>] \
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
#
#   report-finding.sh --type wiki --lens Structure \
#       "Recipe page in Reference section" important \
#       '_Sidebar.md:14, Recipe-Webhook-Receiver.md:1' \
#       'Sections own the triple' \
#       'Recipe-register page filed under the Reference section; register mismatch with siblings.' \
#       < body.md

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

TYPE=""
LENS=""

while [ $# -gt 0 ]; do
    case "$1" in
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
    echo "usage: report-finding.sh --type <code|documentation|wiki> [--lens <name>] <title> <severity> <location> <principle> <summary>  (body on stdin)" >&2
    exit 2
fi

# Strip leading/trailing backticks if the caller wrapped the location — the
# script renders them on write. Authors may pass either form.
LOCATION="${LOCATION#\`}"
LOCATION="${LOCATION%\`}"

case "$TYPE" in
    code|documentation|wiki) ;;
    *)
        echo "report-finding.sh: invalid type '$TYPE' (must be code, documentation, or wiki)" >&2
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

if [ "$TYPE" = "documentation" ] || [ "$TYPE" = "wiki" ]; then
    if [ -z "$LENS" ]; then
        echo "report-finding.sh: --lens is required when --type is $TYPE" >&2
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
        echo "report-finding.sh: --lens applies to --type documentation or --type wiki only" >&2
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

dir=$(findings_dir)
mkdir -p "$dir"

# Auto-suffix on slug collision: -2, -3, -4, ... Writes always succeed.
target="${dir}/${slug}.md"
counter=2
while [ -e "$target" ]; do
    target="${dir}/${slug}-${counter}.md"
    counter=$((counter + 1))
done

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
