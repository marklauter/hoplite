#!/usr/bin/env bash
# Query notes by structured predicates over the head fields.
#
# Each flag is an optional predicate. Multiple flags AND together.
# No flags matches every note.
#
# Predicates:
#   --title PAT     substring, case-insensitive, against the H1 title
#   --tag TAG       exact match against an entry in the comma-separated Tags
#   --xtag TAG      exclude notes where this tag is present in the Tags line
#   --summary PAT   substring, case-insensitive, against the one-line summary
#
# Output: same block-per-match format as list-notes.sh.
# Exit code is 0 whether or not there are matches — a clean empty result is success.
#
# Usage:
#   query.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT]
#
# Examples:
#   query.sh --tag auth-investigation
#   query.sh --title cache --summary ttl
#   query.sh --tag cache --xtag draft
#   query.sh --xtag stale

set -e

TITLE=""
TAG=""
XTAG=""
SUMMARY=""

while [ $# -gt 0 ]; do
    case "$1" in
        --title)
            [ $# -ge 2 ] || { echo "query.sh: --title requires a value" >&2; exit 2; }
            TITLE="$2"; shift 2 ;;
        --tag)
            [ $# -ge 2 ] || { echo "query.sh: --tag requires a value" >&2; exit 2; }
            TAG="$2"; shift 2 ;;
        --xtag)
            [ $# -ge 2 ] || { echo "query.sh: --xtag requires a value" >&2; exit 2; }
            XTAG="$2"; shift 2 ;;
        --summary)
            [ $# -ge 2 ] || { echo "query.sh: --summary requires a value" >&2; exit 2; }
            SUMMARY="$2"; shift 2 ;;
        *)
            echo "query.sh: unknown argument '$1'" >&2
            echo "usage: query.sh [--title PAT] [--tag TAG] [--xtag TAG] [--summary PAT]" >&2
            exit 2 ;;
    esac
done

if [ ! -d docs/notes ]; then
    echo "no notes"
    exit 0
fi

shopt -s nullglob
files=(docs/notes/*.md)

if [ ${#files[@]} -eq 0 ]; then
    echo "no notes"
    exit 0
fi

first=1
matched=0
for f in "${files[@]}"; do
    title=$(sed -n '1s/^# //p' "$f")
    tags=$(sed -n '3s/^Tags: //p' "$f")
    summary=$(sed -n '4p' "$f")
    name=$(basename "$f")

    if [ -n "$TITLE" ]; then
        case "${title,,}" in
            *"${TITLE,,}"*) ;;
            *) continue ;;
        esac
    fi

    if [ -n "$TAG" ]; then
        case ",${tags// /}," in
            *",${TAG},"*) ;;
            *) continue ;;
        esac
    fi

    if [ -n "$XTAG" ]; then
        case ",${tags// /}," in
            *",${XTAG},"*) continue ;;
        esac
    fi

    if [ -n "$SUMMARY" ]; then
        case "${summary,,}" in
            *"${SUMMARY,,}"*) ;;
            *) continue ;;
        esac
    fi

    [ "$first" = "1" ] || echo
    first=0
    matched=1

    echo "$title"
    echo "  tags: $tags"
    echo "  $summary"
    echo "  -> $name"
done

if [ "$matched" = "0" ]; then
    echo "no matches"
fi
