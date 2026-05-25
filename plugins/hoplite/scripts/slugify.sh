#!/usr/bin/env bash
# slugify.sh — convert a string to a URL-safe lowercase slug.
#
# Slug rule (matches the writing-prose reference/ filename convention):
#   1. Lowercase
#   2. Replace non-alphanumerics with dashes
#   3. Collapse runs of dashes into one
#   4. Trim leading and trailing dashes
#   5. Cap at 80 characters
#
# Usage:
#   slugify.sh "Some Title Here"
#   echo "Some Title Here" | slugify.sh
#
# Both forms produce: some-title-here
#
# Edge cases:
#   - "Anticipate the reader's question" → anticipate-the-reader-s-question
#   - "Strong verbs over verb-plus-adverb" → strong-verbs-over-verb-plus-adverb
#   - Empty input or whitespace-only input → empty slug (exits 0, prints nothing)

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  sed -n '2,/^$/p' "$0" | sed 's/^# \?//'
  exit 0
fi

# Read input from argument or stdin
if [[ $# -gt 0 ]]; then
  input="$1"
else
  input=$(cat)
fi

# Lowercase, replace non-alphanumerics with dashes, collapse runs, trim, cap at 80
slug=$(printf '%s' "$input" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' \
  | cut -c1-80)

printf '%s\n' "$slug"
