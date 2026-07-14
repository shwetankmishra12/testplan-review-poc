# Troubleshooting

## Get the real error first

Open **cursor.com/automations** → failed run → copy the last error from the log.

---

## Worker / eligibility

| Symptom | Fix |
|---------|-----|
| No self-hosted workers connected | `agent login` then `agent worker start` from **this repo root** |
| No matching self-hosted worker eligible | Wrong cwd — start worker from `testplan-review-poc`, not `$HOME` or another clone |
| `command not found: agent` | Add `~/.local/bin` to PATH |

See [self-hosted-worker.md](self-hosted-worker.md).

---

## Confluence fetch / auth

| Symptom | Fix |
|---------|-----|
| HTTP 401/403 from fetch script | Refresh PAT; ensure Bearer token works against on-prem Confluence |
| Network / timeout | VPN required from worker Mac to `confluence.cohesity.com` |
| Page not found | Use `?pageId=` URL or exact `/display/SPACE/Title` |

MCP is optional for reads; scripts use REST. Do **not** use MCP for inline comments.

---

## Inline comments fail

| Symptom | Fix |
|---------|-----|
| `Can not create inline comment` | Anchor text must exist in page **storage HTML**; prefer unique phrases |
| Wrong highlight location | Set `match_index` for multi-match anchors, or pick a unique `anchor` |
| HTTP 412 on `/rest/inlinecomments/...` | Use `scripts/post_inline_comments.py` (content API + `location=inline`), not the inlinecomments endpoint alone |

Dry-run:

```bash
python3 ./scripts/post_inline_comments.py --page-id <id> \
  --findings /tmp/testplan-findings.json --dry-run
```

---

## Slack trigger

| Symptom | Fix |
|---------|-----|
| No run at all | Post Confluence URL as **top-level** message in a **public** channel |
| Reply not in thread | Enable **Respond in the triggering thread** |
| Full findings dumped in Slack | Agent Instructions should say Slack = summary only |

---

## What to paste when asking for help

1. Failed run error (last ~20 lines; redact tokens)
2. Worker start directory
3. Whether local `./scripts/fetch_confluence_page.sh` works on the Mac
4. Page id / URL under test
