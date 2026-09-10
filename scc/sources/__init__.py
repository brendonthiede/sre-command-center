"""Every source is a module with NAME, INTERVAL_SECONDS, MAX_AGE_HOURS and fetch() -> list[Item].
Order here is the dashboard order."""
from scc.sources import gcal, github_prs, incidentio, notion, sentry, slack_support

SOURCES = (gcal, sentry, slack_support, incidentio, github_prs, notion)
BY_NAME = {s.NAME: s for s in SOURCES}
