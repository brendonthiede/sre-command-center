"""Unresolved Sentry issues matching the config query, seen in the last 24h. One item per issue.

Default query mirrors the alert workflows that post to #eng-error-monitoring
(production, level >= error, frontend + backend projects); see config.toml.
"""
import urllib.parse

import requests

from scc.config import CFG, secret
from scc.db import Item

NAME = "sentry"
INTERVAL_SECONDS = 300
MAX_AGE_HOURS = 48
LIMIT = 200


def fetch() -> list[Item]:
    url = (f"https://sentry.io/api/0/organizations/{secret('SENTRY_ORG')}/issues/?"
           + urllib.parse.urlencode({"query": CFG["sentry_query"], "statsPeriod": "24h",
                                     "sort": "date", "limit": 100}))
    headers = {"Authorization": f"Bearer {secret('SENTRY_AUTH_TOKEN')}"}
    items: list[Item] = []
    while url and len(items) < LIMIT:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        for iss in r.json():
            items.append(Item(
                external_id=iss["id"],
                title=f"{iss['shortId']} {iss['title']}"[:200],
                url=f"{iss['permalink']}?query=level%3A%5Berror%2Cfatal%5D",
                summary=iss.get("culprit") or "",
                data={"count": int(iss.get("count", 0)), "users": iss.get("userCount", 0),
                      "level": iss.get("level"), "substatus": iss.get("substatus"),
                      "project": (iss.get("project") or {}).get("slug"),
                      "firstSeen": iss.get("firstSeen")},
                source_updated_at=iss.get("lastSeen") or "",
            ))
        nxt = r.links.get("next", {})
        url = nxt.get("url") if nxt.get("results") == "true" else None
    return items
