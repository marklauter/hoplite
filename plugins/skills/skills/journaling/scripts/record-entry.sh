#!/usr/bin/env bash
# Write or extend an engineering-notebook-style journal entry.
#
# Two modes, governed by flags:
#   (none)        new entry. Filename includes date+time prefix:
#                 docs/journal/YYYY-MM-DD-HHMM-<slug>.md. Refuses if a
#                 same-minute same-slug file exists.
#   --append      extend the body of the latest existing entry matching the
#                 slug. Header (H1, date, tags, summary) is preserved. Title
#                 is used only to derive the slug for finding the target.
#
# The journal is historically immutable: there is no --overwrite flag.
# Corrections are new entries that reference and correct the prior one.
#
# Head fields (title, tags, summary) are positional for new entries. The body
# is read from stdin and appended verbatim. The skill documents the body
# shape (Context/Attempted/Outcome/Decision/Next is one default); this
# script does not validate it. Tags may be empty (pass "").
#
# Output discipline:
#   - Success: silent. The file at docs/journal/<filename>.md is the artifact.
#   - Failure: validation error to stderr, non-zero exit.
#
# Usage:
#   record-entry.sh           <title> <tags> <summary> < body.md   # new
#   record-entry.sh --append  <title>                  < body.md   # extend
#
# Examples:
#   record-entry.sh "Verified cache TTL via config" 'auth-investigation,cache' \
#       'Confirmed 300s TTL in appsettings.json; closes stale-read thread.' \
#       < body.md
#   record-entry.sh --append "Verified cache TTL via config" < followup.md

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

APPEND=0

while [ $# -gt 0 ]; do
    case "$1" in
        --append)
            APPEND=1
            shift ;;
        --)
            shift
            break ;;
        --*)
            echo "record-entry.sh: unknown flag '$1'" >&2
            exit 2 ;;
        *)
            break ;;
    esac
done

TITLE="${1:-}"

if [ -z "$TITLE" ]; then
    echo "usage: record-entry.sh [--append] <title> [<tags> <summary>]  (body on stdin)" >&2
    exit 2
fi

if [ "$APPEND" = "1" ]; then
    if [ $# -gt 1 ]; then
        echo "record-entry.sh: --append takes only <title>; got extra positional args" >&2
        exit 2
    fi
else
    TAGS="${2-}"
    SUMMARY="${3:-}"
    if [ -z "$SUMMARY" ]; then
        echo "usage: record-entry.sh <title> <tags> <summary>  (body on stdin)" >&2
        exit 2
    fi
fi

if [ -t 0 ]; then
    echo "record-entry.sh: body must be piped on stdin" >&2
    exit 2
fi

body=$(cat)

if [ -z "${body//[[:space:]]/}" ]; then
    echo "record-entry.sh: body must not be empty" >&2
    exit 2
fi

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
slug=$(bash "$plugin_root/scripts/slugify.sh" "$TITLE")

if [ -z "$slug" ]; then
    echo "record-entry.sh: title slug is empty after sanitization" >&2
    exit 2
fi

mkdir -p docs/journal

if [ "$APPEND" = "1" ]; then
    shopt -s nullglob
    matches=(docs/journal/*-"${slug}".md)
    shopt -u nullglob
    if [ ${#matches[@]} -eq 0 ]; then
        echo "record-entry.sh: no existing entry matching slug '${slug}' (cannot append)" >&2
        exit 2
    fi
    # Pick the latest filename (chronological by date-time prefix)
    target="${matches[${#matches[@]} - 1]}"
    {
        printf '%s' "$body"
        printf '\n'
    } >> "$target"
    exit 0
fi

date_part=$(date +%Y-%m-%d)
time_part=$(date +%H%M)
date_head="${date_part} $(date +%H:%M)"
target="docs/journal/${date_part}-${time_part}-${slug}.md"

if [ -e "$target" ]; then
    echo "record-entry.sh: $target already exists (journal is append-only; choose a more specific title or wait one minute)" >&2
    exit 2
fi

{
    printf '# %s\n\n' "$TITLE"
    printf 'date: %s\n' "$date_head"
    printf 'tags: %s\n' "$TAGS"
    printf '%s\n\n' "$SUMMARY"
    printf '%s\n' "$body"
} > "$target"
