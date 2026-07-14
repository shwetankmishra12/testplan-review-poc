# Self-hosted worker setup (macOS)

Automations that use **My Machines** / self-hosted runtime fail without a worker:

> No self-hosted workers are connected…

Use a Mac with VPN access to `confluence.cohesity.com`.

---

## 1. Install Cursor Agent CLI

```bash
curl https://cursor.com/install -fsS | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
agent --version
```

---

## 2. Clone / open this repo

```bash
cd /Users/shwetank.mishra@cohesity.com/workspace/testplan-review-poc
```

If the automation is linked to GitHub, the worker **must** be started from this
repo directory (not `$HOME`).

---

## 3. Confluence PAT

```bash
export CONFLUENCE_URL=https://confluence.cohesity.com
export CONFLUENCE_PERSONAL_ACCESS_TOKEN=<your-pat>
# or: echo '<pat>' > ~/.confluence_pat && chmod 600 ~/.confluence_pat
```

Do not commit the PAT.

---

## 4. Authenticate + start worker

```bash
cd /Users/shwetank.mishra@cohesity.com/workspace/testplan-review-poc
agent login
agent worker start   # leave terminal open
```

Expected: `Worker is now running` with `Directory:` pointing at this repo.

Confirm under **cursor.com/dashboard → Cloud Agents → My Machines**.

---

## 5. Cursor Automation settings

| Field | Value |
|-------|-------|
| Repository | This GitHub repo (`testplan-review-poc`) |
| Runtime | Self-hosted / My Machines |
| Agent Instructions | Paste `automation/agent-instructions.md` |
| Trigger | Slack channel (top-level messages with Confluence URLs) |
| Slack | Respond in thread; short summary only |

---

## Error: "No matching self-hosted worker is eligible"

Worker is running from the **wrong directory** (often `$HOME` or another repo).

```bash
# Ctrl+C old worker
cd /Users/shwetank.mishra@cohesity.com/workspace/testplan-review-poc
agent worker start
```

Match the GitHub repo configured on the automation.

---

## Smoke test scripts locally

```bash
./scripts/fetch_confluence_page.sh --page-id 1313507592 | head -40
python3 ./scripts/post_inline_comments.py --page-id <sandbox-page-id> \
  --anchor "unique phrase from page" --body "[POC] test" --dry-run
```
