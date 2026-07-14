#!/usr/bin/env python3
"""Post Confluence *inline* comments for test-plan review findings.

MCP has no comment APIs. This uses Confluence Server/DC REST:
  POST /rest/api/content  with extensions.location=inline

Critical: originalSelection must appear in page storage HTML, and
numMatches/matchIndex must match reality. Prefer unique anchors.

Usage:
  export CONFLUENCE_URL=https://confluence.cohesity.com
  export CONFLUENCE_PERSONAL_ACCESS_TOKEN=<pat>

  # Findings JSON file (array):
  # [
  #   {"rule_id":"STG-003","severity":"critical",
  #    "anchor":"Populate MsgFolderRoot",
  #    "message":"Rename DirCustom1 to Migration_Add_Update_Delete_Email",
  #    "match_index":0}
  # ]
  python3 post_inline_comments.py --page-id 1307554771 --findings findings.json

  # Or single comment:
  python3 post_inline_comments.py --page-id 1307554771 \
    --anchor "Color Scheme For Current Epic Review" \
    --body "[META-002] Color scheme explanation looks good (dry-run)."
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html import escape
from typing import Any


def env_token() -> tuple[str, str]:
    base = os.environ.get("CONFLUENCE_URL", "https://confluence.cohesity.com").rstrip("/")
    token = (
        os.environ.get("CONFLUENCE_PERSONAL_ACCESS_TOKEN")
        or os.environ.get("CONFLUENCE_PAT")
        or ""
    )
    if not token and os.path.isfile(os.path.expanduser("~/.confluence_pat")):
        token = open(os.path.expanduser("~/.confluence_pat")).read().strip()
    if not token:
        sys.exit("ERROR: set CONFLUENCE_PERSONAL_ACCESS_TOKEN (or ~/.confluence_pat)")
    return base, token


def api(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Atlassian-Token": "no-check",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {body[:800]}") from e


def strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def find_anchor(storage_html: str, preferred: str, fallback_needles: list[str]) -> tuple[str, int, int]:
    """Return (anchor, num_matches, match_index). Prefer unique preferred text."""
    candidates: list[str] = []
    if preferred:
        candidates.append(preferred.strip())
    candidates.extend(n.strip() for n in fallback_needles if n and n.strip())

    # Also try shorter suffixes of preferred (last 40–80 chars) for uniqueness
    if preferred and len(preferred) > 80:
        candidates.append(preferred.strip()[-80:])
        candidates.append(preferred.strip()[:80])

    for cand in candidates:
        n = storage_html.count(cand)
        if n == 1:
            return cand, 1, 0
        if n > 1:
            # First occurrence; caller may override match_index
            return cand, n, 0

    # Last resort: pick a unique 40+ char text node near preferred keywords
    nodes = re.findall(r">([^<]{30,100})<", storage_html)
    for node in nodes:
        t = node.strip()
        if not t:
            continue
        if preferred and preferred[:20].lower() in t.lower() and storage_html.count(t) == 1:
            return t, 1, 0
    for node in nodes:
        t = node.strip()
        if t and storage_html.count(t) == 1:
            return t, 1, 0

    raise RuntimeError(
        f"Could not find usable inline anchor for preferred={preferred!r}. "
        "Anchor text must exist in page storage HTML."
    )


def post_inline(
    base: str,
    token: str,
    page_id: str,
    anchor: str,
    body_html: str,
    num_matches: int,
    match_index: int,
) -> dict:
    now = str(int(time.time() * 1000))
    payload = {
        "type": "comment",
        "container": {"id": str(page_id), "type": "page"},
        "body": {"storage": {"value": body_html, "representation": "storage"}},
        "extensions": {
            "location": "inline",
            "inlineProperties": {
                "originalSelection": anchor,
                "numMatches": int(num_matches),
                "matchIndex": int(match_index),
                "lastFetchTime": now,
                "serializedHighlights": json.dumps([[anchor]]),
            },
        },
    }
    return api("POST", f"{base}/rest/api/content", token, payload)


def format_comment(finding: dict) -> str:
    rule = escape(str(finding.get("rule_id", "FINDING")))
    sev = escape(str(finding.get("severity", "medium")).upper())
    msg = escape(str(finding.get("message", "")).strip())
    fix = escape(str(finding.get("fix", "")).strip())
    # Omit location — inline highlight already shows where the finding is.
    parts = [
        f"<p><strong>[{rule}]</strong> · {sev}</p>",
        f"<p>{msg}</p>" if msg else "",
    ]
    if fix:
        parts.append(f"<p><em>Suggested fix:</em> {fix}</p>")
    parts.append(
        "<p><em>Posted by Test Plan Standardization Review bot</em></p>"
    )
    return "".join(p for p in parts if p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--page-id", required=True)
    ap.add_argument("--findings", help="JSON file with findings array")
    ap.add_argument("--anchor", help="Single-comment anchor text")
    ap.add_argument("--body", help="Single-comment body (plain text)")
    ap.add_argument("--match-index", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base, token = env_token()
    page = api(
        "GET",
        f"{base}/rest/api/content/{args.page_id}?expand=body.storage,version,title",
        token,
    )
    storage = page["body"]["storage"]["value"]
    title = page.get("title", "")
    print(f"Page: {title} (id={args.page_id}, ver={page['version']['number']})", file=sys.stderr)

    findings: list[dict[str, Any]]
    if args.findings:
        findings = json.load(open(args.findings))
        if not isinstance(findings, list):
            sys.exit("findings file must be a JSON array")
    elif args.anchor and args.body:
        findings = [
            {
                "rule_id": "MANUAL",
                "severity": "info",
                "anchor": args.anchor,
                "message": args.body,
                "match_index": args.match_index,
            }
        ]
    else:
        sys.exit("Provide --findings FILE or --anchor + --body")

    results = []
    for i, f in enumerate(findings):
        preferred = str(f.get("anchor") or f.get("location") or "")
        fallbacks = [
            str(f.get("location") or ""),
            str(f.get("section") or ""),
            str(f.get("rule_id") or ""),
        ]
        try:
            anchor, nmatch, _ = find_anchor(storage, preferred, fallbacks)
            match_index = int(f.get("match_index", args.match_index))
            if match_index >= nmatch:
                match_index = 0
            body_html = format_comment(f)
            print(
                f"[{i}] {f.get('rule_id')} anchor={anchor!r} matches={nmatch} index={match_index}",
                file=sys.stderr,
            )
            if args.dry_run:
                results.append({"dry_run": True, "anchor": anchor, "rule_id": f.get("rule_id")})
                continue
            created = post_inline(
                base, token, args.page_id, anchor, body_html, nmatch, match_index
            )
            results.append(
                {
                    "ok": True,
                    "comment_id": created.get("id"),
                    "rule_id": f.get("rule_id"),
                    "anchor": anchor,
                    "webui": (created.get("_links") or {}).get("webui"),
                }
            )
            print(f"  -> comment {created.get('id')}", file=sys.stderr)
            time.sleep(0.3)  # be gentle
        except Exception as e:
            results.append(
                {
                    "ok": False,
                    "rule_id": f.get("rule_id"),
                    "anchor_preferred": preferred,
                    "error": str(e),
                }
            )
            print(f"  -> FAIL {e}", file=sys.stderr)

    print(json.dumps({"page_id": args.page_id, "title": title, "results": results}, indent=2))
    failed = sum(1 for r in results if not r.get("ok") and not r.get("dry_run"))
    sys.exit(1 if failed and not args.dry_run else 0)


if __name__ == "__main__":
    main()
