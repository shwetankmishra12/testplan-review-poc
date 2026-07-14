#!/usr/bin/env bash
# Fetch Confluence page body via REST API (POC fallback when MCP unavailable).
#
# Setup (same terminal before agent worker start):
#   export CONFLUENCE_URL=https://confluence.cohesity.com
#   export CONFLUENCE_PERSONAL_ACCESS_TOKEN=<your-pat>
#
# Usage:
#   ./fetch_confluence_page.sh "<confluence-url>"
#   ./fetch_confluence_page.sh --page-id 1307554771
#   ./fetch_confluence_page.sh --verbose "<url>"

set -euo pipefail

VERBOSE=0
if [[ "${1:-}" == "--verbose" || "${1:-}" == "-v" ]]; then
  VERBOSE=1
  shift
fi

CONFLUENCE_URL="${CONFLUENCE_URL:-https://confluence.cohesity.com}"
CONFLUENCE_URL="${CONFLUENCE_URL%/}"
TOKEN="${CONFLUENCE_PERSONAL_ACCESS_TOKEN:-${CONFLUENCE_PAT:-}}"

# Optional: store PAT in ~/.confluence_pat (chmod 600) — do not commit
if [[ -z "$TOKEN" && -f "${HOME}/.confluence_pat" ]]; then
  TOKEN="$(tr -d '[:space:]' < "${HOME}/.confluence_pat")"
fi

die() {
  echo "ERROR: $*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

need_cmd curl
need_cmd python3

if [[ -z "$TOKEN" ]]; then
  die "set CONFLUENCE_PERSONAL_ACCESS_TOKEN (or CONFLUENCE_PAT, or ~/.confluence_pat)"
fi

curl_api() {
  local url="$1"
  local out http_code body
  out="$(mktemp)"
  http_code="$(curl -sS -w "%{http_code}" -o "$out" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/json" \
    "$url")" || die "curl network error for ${url}"
  body="$(cat "$out")"
  rm -f "$out"
  if [[ "$VERBOSE" == 1 ]]; then
    echo "GET ${url} -> HTTP ${http_code}" >&2
  fi
  if [[ "$http_code" != "200" ]]; then
    echo "HTTP ${http_code} from Confluence API" >&2
    echo "${body}" >&2
    die "Confluence API request failed (check VPN, PAT, and URL)"
  fi
  printf '%s' "$body"
}

page_id=""
input="${1:-}"
input="${input%%$'\r'}"
input="$(echo "$input" | sed -E 's/[[:space:]]+$//')"

if [[ -z "$input" ]]; then
  die "usage: $0 [--verbose] <confluence-url> | --page-id <id>"
fi

if [[ "$input" == "--page-id" ]]; then
  page_id="${2:-}"
  [[ -n "$page_id" ]] || die "missing page id after --page-id"
elif [[ "$input" =~ pageId=([0-9]+) ]]; then
  page_id="${BASH_REMATCH[1]}"
elif [[ "$input" =~ /display/([^/]+)/(.+) ]]; then
  space_key="${BASH_REMATCH[1]}"
  title="${BASH_REMATCH[2]//+/ }"
  title="$(python3 -c "import urllib.parse,sys; print(urllib.parse.unquote(sys.argv[1]))" "$title")"
  cql="space=\"${space_key}\" AND title=\"${title}\" AND type=page"
  enc="$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$cql")"
  search="$(curl_api "${CONFLUENCE_URL}/rest/api/content/search?cql=${enc}&limit=1")"
  page_id="$(python3 -c "
import json,sys
d=json.load(sys.stdin)
r=d.get('results') or []
print(r[0]['id'] if r else '')
" <<<"$search")"
  if [[ -z "$page_id" ]]; then
    die "page not found: space=${space_key} title=${title}"
  fi
else
  die "unsupported URL; use /display/SPACE/Title or ?pageId=NUM"
fi

curl_api "${CONFLUENCE_URL}/rest/api/content/${page_id}?expand=body.storage,version,space" \
  | python3 -m json.tool
