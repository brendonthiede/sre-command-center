# SRE Command Center design (2026-09-10)

## Design

**One process, one file of state.** `uv run scc serve` starts a Flask app on `127.0.0.1:8765` and a background thread that runs each source's `sync()` on its own interval. `uv run scc sync <source>` runs one sync in the foreground for testing. State lives in `data/scc.db` (gitignored).

**One generic item table.** Every source normalizes into the same row so the dashboard, notes, and status handling are written once:

```sql
items(
  source TEXT, external_id TEXT,          -- PK together
  title TEXT, url TEXT, summary TEXT,
  data TEXT,                              -- JSON blob of source-specific fields (counts, assignee, etc.)
  first_seen TEXT, last_seen TEXT, source_updated_at TEXT,
  status TEXT DEFAULT 'new',              -- new | watching | delegated | ticketed | done
  note TEXT DEFAULT '',
  snoozed_until TEXT,
  PRIMARY KEY (source, external_id)
)
sync_runs(source TEXT PRIMARY KEY, ran_at TEXT, ok INTEGER, message TEXT)
```

Sync is an upsert: new rows get `status='new'`; existing rows keep `status`/`note` and refresh title/url/summary/data/last_seen. Items no longer returned by the source are not deleted; the dashboard hides items with `status='done'` and items whose `last_seen` is older than a per-source window. Nothing is ever pushed back to a source in v1 (no archiving in Sentry, no closing follow-ups); every item links out.

**Sources** are plain modules under `scc/sources/`, each exposing `NAME`, `INTERVAL_SECONDS`, and `fetch() -> list[Item]`. No base class, no registry: `scc/sources/__init__.py` lists them in a tuple.

| Source | How | Item |
|---|---|---|
| `sentry` | `GET https://sentry.io/api/0/organizations/{org}/issues/?query=is:unresolved&statsPeriod=24h` with `SENTRY_AUTH_TOKEN` | one per issue; data = count, userCount, lastSeen, level, substatus |
| `github_prs` | `subprocess` call to `gh search prs --owner augusthealth --state open --label ops --json ...` (reuses gh auth, no token handling) | one per PR; data = repo, author, updatedAt, reviewDecision |
| `slack_support` | `conversations.history` on the support channel since last run; `conversations.replies` for reply count | one per top-level message; data = author, reply_count, last_reply_ts |
| `incidentio` | `GET /v2/incidents` with `status_category[one_of]=learning`, and `GET /v3/follow_ups` paged, filtered client-side to `outstanding` | two item kinds: `incident:<id>` (data = has_debrief, has_postmortem, manual `timeline_reviewed` flag stored in note/status) and `followup:<id>` (data = assignee, priority, incident ref) |
| `gcal` | Google Calendar API, all calendars in the account's calendarList with `selected=true`, events from now to +48h | one per event; data = calendar name, start, end, attendees count. Events are display-only (no notes needed) |
| `notion` | `claude -p` with `--allowedTools` limited to Notion query tools, `--output-format json`, prompt asks for a JSON array of tasks assigned to Brendon from the configured database URL | one per task; data = due date, status, page URL |

**Config.** Secrets in `.env` (gitignored, loaded by `scc/config.py` with a ten-line parser, no dependency). Non-secret settings in `config.toml` (stdlib `tomllib`): Slack channel ID, Notion database URL, GitHub org, NAS `user@host:/path`, calendar exclusions. `config.example.toml` and `.env.example` are committed.

**Dashboard.** One Jinja template, sections per source ordered: calendar (today), Sentry, Slack support, incident.io, PRs, Notion. Each item row shows title, age, source-specific badges, current status, and a note snippet. Clicking a row expands an inline form: status select, note textarea, snooze-until date, save. Plain HTML forms with POST and redirect. No JS framework; a few lines of vanilla JS to toggle the expander. A "Sync now" button per section calls the source synchronously.

**Backup.** `uv run scc backup` uses `sqlite3.Connection.backup()` to write `data/scc-backup.db`, then `rsync -a` to the configured NAS target. The scheduler thread calls it once a day; it also runs on demand.

**Dependencies.** `flask`, `requests`, `google-api-python-client`, `google-auth-oauthlib`. Everything else is stdlib.

**Skipped on purpose (v1):** auth on the web page (loopback only), pushing changes back to sources, Slack error channel, incident.io post-incident tasks (not in public API), systemd service, tests beyond one self-check per non-trivial module.

