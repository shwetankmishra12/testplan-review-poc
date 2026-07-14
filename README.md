# Test Plan Standardization Review (POC)

On-demand reviewer for **O365 mailbox** Confluence test plans.

Triggered from Slack → grades the plan against a Confluence checklist → posts
**inline comments** on the page. Slack gets only a short summary.

## Layout

```text
scripts/           Worker runtime (fetch page, post inline comments)
standards/         Local YAML mirror of rules (fallback)
automation/        Cursor Automation agent instructions (paste into UI)
docs/              Setup + troubleshooting
examples/          Sample findings JSON / Slack summary
```

## Prerequisites

- Self-hosted Cursor worker on a Mac with VPN to `confluence.cohesity.com`
- Confluence PAT in **`~/.confluence_pat`** (agent shells often do not inherit `export`)
- Cursor Automation linked to **this** GitHub repo
- Standards checklist:
  https://confluence.cohesity.com/pages/viewpage.action?pageId=1313507592

Confluence MCP **cannot** create inline comments. Use `scripts/post_inline_comments.py`.

## Quick start (Mac worker)

```bash
cd /Users/shwetank.mishra@cohesity.com/workspace/testplan-review-poc

# Required — file, not just shell export (automation shells strip env)
echo '<pat>' > ~/.confluence_pat && chmod 600 ~/.confluence_pat

agent login
agent worker start   # leave terminal open; start from THIS repo root
```

In Cursor Automation → **Agent Instructions**, paste only
`automation/BOOTSTRAP.md` (short). The agent then reads
`automation/agent-instructions.md` from the repo on each run.

## Manual smoke test

```bash
./scripts/fetch_confluence_page.sh --page-id 1313507592 | head
python3 ./scripts/post_inline_comments.py --page-id <page_id> \
  --anchor "unique text from page" \
  --body "[POC] smoke test" \
  --dry-run
```

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/self-hosted-worker.md](docs/self-hosted-worker.md) | Install / login / start worker |
| [docs/architecture.md](docs/architecture.md) | Why REST, not MCP |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common failures |
| [automation/agent-instructions.md](automation/agent-instructions.md) | Prompt for Cursor Automation |
