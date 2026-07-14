# Architecture

## Goal

Review O365 mailbox Confluence test plans against a standards checklist and
post **inline** findings on the page (text-anchored highlights).

## Why not MCP for comments?

| Tool | Can read pages? | Can post **inline** comments? |
|------|-----------------|-------------------------------|
| Confluence MCP (`user-confluence-mcp`) | Yes | **No** — no comment APIs |
| Atlassian Cloud MCP | N/A for on-prem | Wrong product |
| Footer comment (`type=comment`) | — | Yes, but not inline |
| REST `POST /rest/api/content` + `location=inline` | — | **Yes** (used here) |

So the worker uses:

1. `scripts/fetch_confluence_page.sh` — read page via REST (Bearer PAT)
2. Agent grades against checklist page `1313507592` (and/or `standards/*.yaml`)
3. `scripts/post_inline_comments.py` — create inline comments via REST

## Inline comment requirements (Server/DC)

Payload must include:

- `extensions.location = "inline"`
- `inlineProperties.originalSelection` — text that exists in storage HTML
- `numMatches` / `matchIndex` matching reality (prefer unique anchors)
- `lastFetchTime` — epoch ms as string
- `serializedHighlights` — `json.dumps([[selection]])`

## Runtime

Cursor Automations do not support Gerrit. Link this **GitHub** repo, run a
**self-hosted** worker from the repo root (corp VPN → Confluence).

Slack is trigger + short summary only; Confluence inline comments are the
deliverable.
