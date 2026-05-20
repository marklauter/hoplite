#!/usr/bin/env bash
# Write or extend a wiki-style note at docs/notes/<slug>.md.
#
# Three modes, governed by flags:
#   (none)        new note. Refuses to write if the target file exists.
#   --overwrite   replace existing note (full header + body) with new content.
#   --append      extend existing note's body. Header is preserved. Title is
#                 used only to derive the slug for finding the target.
#
# --overwrite and --append are mutually exclusive.
#
# Head fields (title, tags, summary) are positional. The body is read from
# stdin and appended verbatim. The skill documents the body shape; this script
# does not validate it. Tags may be empty (pass "").
#
# Output discipline:
#   - Success: silent. The file at docs/notes/<slug>.md is the artifact.
#   - Failure: validation error to stderr, non-zero exit.
#
# Usage:
#   record-note.sh                <title> <tags> <summary> < body.md   # new
#   record-note.sh --overwrite    <title> <tags> <summary> < body.md   # replace
#   record-note.sh --append       <title>                  < body.md   # extend
#
# Examples:
#   record-note.sh "Cache TTL is 300s" 'auth-investigation,cache' \
#       'Confirmed via appsettings.json; stale read was a cold-start artifact.' \
#       < body.md
#   record-note.sh --append "Cache TTL is 300s" < followup.md

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

OVERWRITE=0
APPEND=0

while [ $# -gt 0 ]; do
    case "$1" in
        --overwrite)
            OVERWRITE=1
            shift ;;
        --append)
            APPEND=1
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

if [ "$OVERWRITE" = "1" ] && [ "$APPEND" = "1" ]; then
    echo "record-note.sh: --overwrite and --append are mutually exclusive" >&2
    exit 2
fi

TITLE="${1:-}"

if [ -z "$TITLE" ]; then
    echo "usage: record-note.sh [--overwrite | --append] <title> [<tags> <summary>]  (body on stdin)" >&2
    exit 2
fi

if [ "$APPEND" = "1" ]; then
    if [ $# -gt 1 ]; then
        echo "record-note.sh: --append takes only <title>; got extra positional args" >&2
        exit 2
    fi
else
    TAGS="${2-}"
    SUMMARY="${3:-}"
    if [ -z "$SUMMARY" ]; then
        echo "usage: record-note.sh [--overwrite] <title> <tags> <summary>  (body on stdin)" >&2
        exit 2
    fi
fi

if [ -t 0 ]; then
    echo "record-note.sh: body must be piped on stdin" >&2
    exit 2
fi

body=$(cat)

if [ -z "${body//[[:space:]]/}" ]; then
    echo "record-note.sh: body must not be empty" >&2
    exit 2
fi

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
slug=$(bash "$plugin_root/scripts/slugify.sh" "$TITLE")

if [ -z "$slug" ]; then
    echo "record-note.sh: title slug is empty after sanitization" >&2
    exit 2
fi

mkdir -p docs/notes
target="docs/notes/${slug}.md"

if [ "$APPEND" = "1" ]; then
    if [ ! -e "$target" ]; then
        echo "record-note.sh: $target does not exist (cannot append)" >&2
        exit 2
    fi
    {
        printf '%s' "$body"
        printf '\n'
    } >> "$target"
    exit 0
fi

if [ -e "$target" ] && [ "$OVERWRITE" != "1" ]; then
    echo "record-note.sh: $target already exists (use --overwrite to replace or --append to extend)" >&2
    exit 2
fi

{
    printf '# %s\n\n' "$TITLE"
    printf 'tags: %s\n' "$TAGS"
    printf '%s\n\n' "$SUMMARY"
    printf '%s\n' "$body"
} > "$target"
