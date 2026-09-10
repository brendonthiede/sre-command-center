"""Every source is a module with NAME, INTERVAL_SECONDS, MAX_AGE_HOURS and fetch() -> list[Item]."""
from scc.sources import github_prs, sentry

SOURCES = (sentry, github_prs)
BY_NAME = {s.NAME: s for s in SOURCES}
