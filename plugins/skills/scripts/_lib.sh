#!/usr/bin/env bash
# Shared helpers for the reviewer scripts (list-findings.sh, query.sh,
# summarize.sh, and any future reviewer additions).
#
# This file is sourced, not executed. It defines functions that read fields
# from the canonical finding-head shape:
#
#   # <title>             ← line 1
#   <blank>                ← line 2
#   Severity: <level>      ← typed fields in any order
#   Type: <kind>
#   Lens: <name>           ← (documentation findings only)
#   Location: <ref>
#   Principle: <text>
#   <summary>              ← line immediately after Principle:
#   <blank>                ← then the body sections
#   ...
#
# The head fields are name-indexed (parsed by label, not line number) so the
# field order is allowed to drift without breaking the readers. The one
# positional rule is the summary line, which is read by offset from the
# Principle: line.

# Extract a typed-field value by its label. Returns empty string if absent.
get_field() {
    local file="$1"
    local field="$2"
    grep -m1 "^${field}: " "$file" | sed "s/^${field}: //" || true
}

# Extract the one-line summary that follows the Principle: line.
# Returns empty string if no Principle: line is present.
get_summary() {
    local file="$1"
    local principle_line
    principle_line=$(grep -n -m1 '^Principle: ' "$file" | cut -d: -f1)
    [ -n "$principle_line" ] || return 0
    sed -n "$((principle_line + 1))p" "$file"
}
