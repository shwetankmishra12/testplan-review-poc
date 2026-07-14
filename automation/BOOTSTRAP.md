# Paste this into Cursor Automation → Agent Instructions
#
# Keep this short. Full workflow lives in-repo and is the source of truth.
# Update the repo file to change behavior — no need to re-paste the long prompt
# unless this bootstrap itself changes.

---

You are triggered from Slack when a message contains a Confluence URL
(`confluence.cohesity.com`).

1. Open and **follow exactly** the file in this repository:
   `automation/agent-instructions.md`
2. Do not invent a parallel workflow. If that file and this note conflict, the
   repo file wins.
3. Ignore bot messages. Process human messages that include a Confluence URL.
4. Use repo scripts under `scripts/` (or `testplan-review-poc/scripts/` if nested).
5. Credentials come from environment secrets / `~/.confluence_pat` — do not ask
   the user to paste a PAT in Slack.
