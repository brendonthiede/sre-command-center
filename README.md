# SRE Command Center

Local dashboard for the feeds I check every day: calendar, Sentry errors, the Slack support
channel, incident.io post-incident work and follow-ups, `ops`-labeled PRs, Notion to-dos.
Each item keeps a status and a note across restarts. Design: `docs/superpowers/specs/`.

## Run

```sh
cp config.example.toml config.toml   # edit channel ID, Notion DB URL, NAS target
cp .env.example .env                 # add tokens (Sentry vars may already be in your shell)
uv run scc serve                     # http://127.0.0.1:8765
uv run scc sync <source>             # one source in the foreground, prints the count
uv run scc backup                    # sqlite backup to data/, rsync to NAS if configured
```

State is `data/scc.db` (gitignored). Background syncs run on each source's own interval;
a section shows FAILED with the reason when a credential is missing, and everything else keeps working.

## Credentials per source

| Source | Needs |
|---|---|
| `sentry` | `SENTRY_ORG`, `SENTRY_AUTH_TOKEN` in env or `.env`. Query is `sentry_query` in config. |
| `github_prs` | `gh auth login`. Repos in `github_repos`. |
| `slack_support` | Slack app with **user** token scopes `channels:history`, `channels:read` (`groups:*` if the channel is private) as `SLACK_USER_TOKEN`; channel ID in `slack_support_channel`. |
| `incidentio` | API key with incident + follow-up read as `INCIDENTIO_API_KEY`. |
| `gcal` | Desktop OAuth client JSON saved as `credentials.json` in the repo root; first sync opens a browser and writes `token.json`. Share work calendars into this Google account. |
| `notion` | Nothing local: runs `claude -p` against the Notion connector hourly (~$0.05/run on Haiku). Database URL in `notion_database_url`. |

## Statuses

`new` → `watching` / `delegated` / `ticketed` → `done`. Done items and snoozed items are hidden.
Items the source stops returning age out of view after each source's `MAX_AGE_HOURS`.

## Adding a source

Copy any module in `scc/sources/`, keep `NAME`, `INTERVAL_SECONDS`, `MAX_AGE_HOURS`, `fetch()`,
and add it to the tuple in `scc/sources/__init__.py`. Nothing else changes.
