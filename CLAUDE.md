# SRE Command Center: agent notes

Local Flask dashboard + sqlite that polls six feeds Brendon monitors daily. Read `README.md`
for usage and `docs/superpowers/specs/` for the design. Ponytail rules apply: stdlib first,
one generic `items` table, no base classes, one self-check per non-trivial module.

## Run and validate

```sh
uv run python -m pytest -q          # 2 self-checks (db upsert semantics, quiet hours)
uv run scc sync <source>            # foreground sync, prints "<source>: N items"
uv run scc serve                    # http://127.0.0.1:8765 ; logs "synced X: N items" per pass
uv run scc backup                   # sqlite backup + scp -O to the Synology
```

To restart the server from a shell command, stop it in a SEPARATE command from the one that
starts it: `pkill -f "[s]cc serve"` matches any shell whose command line also contains
`scc serve`, including the one running the restart, and kills it (exit 144).

Secrets live in `.env` (gitignored): `SENTRY_*`, `SLACK_USER_TOKEN` (xoxp), `SLACK_CLIENT_ID/SECRET`,
`INCIDENTIO_API_KEY`. `credentials.json` + `token.json` in the repo root are the Google OAuth
client and its token. Settings in `config.toml` (gitignored; `config.example.toml` is the template).

## Non-obvious constraints, per source

- **sentry**: the query mirrors the Sentry alert workflows that post to #eng-error-monitoring
  (production, level >= error, frontend + backend). Read the workflows with
  `GET /api/0/organizations/$SENTRY_ORG/workflows/`; the older `rules/` endpoints are gone.
  Event-attribute exclusions in those workflows (401/403, some pharmacy messages) cannot be
  expressed in issue search, so a few of those issues still appear.
- **github_prs**: uses per-repo `gh pr list`, not `gh search prs`. The search index returns
  `incomplete_results=true` under load and drops PRs; repeated probes also trip GitHub's
  secondary rate limit.
- **slack_support**: `oldest` MUST be an int. Slack returns an empty list, no error, when it has
  more than six decimal places. Author names need `users:read`, which the app does not have.
  The app (A0C0VERHY9K, "SRE Command Center") was created via `apps.manifest.create` using the
  Slack CLI's session token; `slack-app/oauth.py` runs the one-click user OAuth on localhost:8790.
  The Slack CLI's own token is `xoxe.xoxp-...` and only carries app-config scopes; never use it
  as `SLACK_USER_TOKEN`.
- **incidentio**: post-incident tasks are not in the public API. `status_category=learning`
  plus `has_debrief` / `postmortem_document_url` is all we get. Follow-ups v3 has no server-side
  status filter; filter `outstanding` client-side.
- **notion**: no PAT is available in the workspace, so a headless `claude -p` run with the
  Notion MCP does the query (~$0.05-0.11 per run on Haiku). The prompt MUST precede
  `--allowedTools`, which is variadic and swallows a trailing prompt. Trust the small model's SQL
  query results, not its summaries: asked to describe the database it invented sample rows.
  `notion_filter` is plain English applied by Claude. Debug with `--output-format stream-json
  --verbose` to see tool calls.
- **gcal**: personal Gmail OAuth client; work calendars are shared into that account. First run
  of `_creds()` opens a browser, so run `scc sync gcal` in the foreground before starting the
  server when `token.json` is missing.
- **backup**: the Synology has neither the rsync service nor the SFTP subsystem enabled for this
  user, so `scp -O` (legacy protocol) is the only thing that works without NAS changes.

## Scheduler

`scc/web.py::_scheduler` runs each source at `INTERVAL_SECONDS`, sleeps 30s between passes,
skips everything during `quiet_hours` (default 19:00-07:00 local), and runs the backup daily.
Failures are recorded in `sync_runs` and shown as FAILED on the dashboard; other sources continue.

## Ideas not done (ask before building)

- `users:read` scope so Slack authors show names instead of IDs (needs re-authorize via oauth.py).
- Notion: a Person property on the to-do database would allow "assigned to me" across databases.
- Pushing changes back to sources (archive in Sentry, close follow-ups) was deliberately skipped.
