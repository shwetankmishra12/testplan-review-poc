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

## Cloud worker vs private worker (most common “token missing” cause)

If the run log says **cloud worker** and `no ~/.confluence_pat`, the automation
did **not** run on your Mac. Cursor Cloud VMs have no corp VPN and no your PAT.

| Where it ran | Can grade somehow? | Can post inline comments? |
|--------------|--------------------|---------------------------|
| Cursor **Cloud** | Sometimes (wrong path / cached) | **No** |
| **Self-hosted** Mac worker + `~/.confluence_pat` | Yes via REST scripts | **Yes** |

**Fix in Cursor Automation settings:**

1. Open the automation → **Runtime** / **Machine**
2. Select **Self-hosted** / **My Machines** / your private worker  
   (do **not** leave “Cloud” / default cloud pool)
3. On Mac:
   ```bash
   echo '<pat>' > ~/.confluence_pat && chmod 600 ~/.confluence_pat
   cd /Users/shwetank.mishra@cohesity.com/workspace/testplan-review-poc
   agent worker start
   ```
4. Confirm dashboard → My Machines shows your host **Idle/Active**
5. Re-trigger Slack with the Confluence URL

Also re-paste `automation/agent-instructions.md` (Step 0 probe aborts early on cloud).

---

## Confluence fetch / auth

| Symptom | Fix |
|---------|-----|
| Token not set / 0 comments posted though export exists in worker shell | Agent shells strip env — put PAT in `~/.confluence_pat` (chmod 600) |
| HTTP 401/403 from fetch script | Refresh PAT; ensure Bearer token works against on-prem Confluence |
| Network / timeout | VPN required from worker Mac to `confluence.cohesity.com` |
| Page not found | Use `?pageId=` URL or exact `/display/SPACE/Title` |

MCP is optional for reads; scripts use REST. Do **not** use MCP for inline comments.

### Env export vs file

`export CONFLUENCE_PERSONAL_ACCESS_TOKEN=...` in the `agent worker start` terminal
does **not** reliably reach commands the automation runs. Scripts already support:

```bash
~/.confluence_pat
```

That is the supported setup for self-hosted workers.

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
