#!/usr/bin/env bash
# Enumerate triage candidates for review.
#
# Filters:
#   unlabeled         issues with no labels at all
#   no-priority       no label whose name begins with "priority"
#   no-area           no label whose name begins with "area" by default,
#                     or no label in AREA_LABELS when that env var is set
#   stale             no activity in STALE_DAYS days (default 90)
#   noise-candidates  no labels, zero comments, body shorter than
#                     NOISE_BODY_CHARS (default 200) or empty
#
# Output discipline:
#   - Success with candidates: one line per issue, format `#<n> [<state>] [<labels>] <title>  <url>`.
#   - Success with no candidates: `no candidates`.
#   - Failure: full captured gh output, exit with gh's code.
#
# Usage:
#   triage-list.sh                 default filter: unlabeled
#   triage-list.sh unlabeled
#   triage-list.sh no-priority
#   triage-list.sh no-area
#   AREA_LABELS="serialization,transactions,core" triage-list.sh no-area
#   triage-list.sh stale
#   STALE_DAYS=180 triage-list.sh stale
#   triage-list.sh noise-candidates
#   NOISE_BODY_CHARS=400 triage-list.sh noise-candidates

set -eo pipefail

case "${1:-}" in
    --help|-h)
        awk 'NR==1 {next} /^#/ {sub(/^#/, ""); sub(/^ /, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
        exit 0
        ;;
esac

FILTER="${1:-unlabeled}"

FORMAT='.[] | "#\(.number) [\(.state)] " + (if (.labels|length)>0 then "[" + ([.labels[].name] | join(",")) + "] " else "" end) + "\(.title)  \(.url)"'

days_ago() {
    days="$1"
    if date -u -v-"${days}d" +%Y-%m-%d >/dev/null 2>&1; then
        date -u -v-"${days}d" +%Y-%m-%d
    else
        date -u -d "-${days} days" +%Y-%m-%d
    fi
}

case "$FILTER" in
    unlabeled)
        args=(issue list --state open --search "no:label" --json number,state,labels,title,url --limit 100 --jq "$FORMAT")
        ;;
    no-priority)
        SELECT='[.[] | select(all(.labels[]; .name | startswith("priority") | not))]'
        args=(issue list --state open --json number,state,labels,title,url --limit 200 --jq "$SELECT | $FORMAT")
        ;;
    no-area)
        if [ -n "${AREA_LABELS:-}" ]; then
            AREA_JSON=$(printf '%s' "$AREA_LABELS" | awk -F, '{ for (i=1;i<=NF;i++) { gsub(/"/,"\\\"",$i); printf "%s\"%s\"", (i>1?",":""), $i } }')
            SELECT="[.[] | select(all(.labels[]; .name as \$n | [${AREA_JSON}] | any(. == \$n) | not))]"
        else
            SELECT='[.[] | select(all(.labels[]; .name | startswith("area") | not))]'
        fi
        args=(issue list --state open --json number,state,labels,title,url --limit 200 --jq "$SELECT | $FORMAT")
        ;;
    stale)
        DAYS="${STALE_DAYS:-90}"
        CUTOFF=$(days_ago "$DAYS")
        args=(issue list --state open --search "updated:<$CUTOFF" --json number,state,labels,title,url --limit 100 --jq "$FORMAT")
        ;;
    noise-candidates)
        THRESHOLD="${NOISE_BODY_CHARS:-200}"
        SELECT="[.[] | select((.labels|length) == 0 and (.comments|length) == 0 and (.body|length) < ${THRESHOLD})]"
        args=(issue list --state open --json number,state,labels,title,url,body,comments --limit 200 --jq "$SELECT | $FORMAT")
        ;;
    *)
        echo "usage: triage-list.sh [unlabeled|no-priority|no-area|stale|noise-candidates]" >&2
        exit 2
        ;;
esac

output=$(gh "${args[@]}" 2>&1) || { code=$?; echo "$output"; exit $code; }

if [ -z "$output" ]; then
    echo "no candidates"
else
    echo "$output"
fi
