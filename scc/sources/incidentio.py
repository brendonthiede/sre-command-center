"""incident.io: incidents in the post-incident ('learning') flow, plus every outstanding follow-up.

Post-incident tasks are not in the public API; the incident item shows the debrief and
postmortem flags and you track timeline review by hand via status/note.
"""
import requests

from scc.config import secret
from scc.db import Item

NAME = "incidentio"
INTERVAL_SECONDS = 900
MAX_AGE_HOURS = 24 * 7
API = "https://api.incident.io"
_incident_cache: dict[str, dict] = {}


def _get(path: str, **params) -> dict:
    r = requests.get(f"{API}{path}", params=params, timeout=30,
                     headers={"Authorization": f"Bearer {secret('INCIDENTIO_API_KEY')}"})
    r.raise_for_status()
    return r.json()


def _paged(path: str, key: str, **params) -> list[dict]:
    out: list[dict] = []
    after = None
    while True:
        body = _get(path, page_size=100, **({"after": after} if after else {}), **params)
        out += body[key]
        after = (body.get("pagination_meta") or {}).get("after")
        if not after or not body[key]:
            return out


def _incident(inc_id: str) -> dict:
    if inc_id not in _incident_cache:
        _incident_cache[inc_id] = _get(f"/v2/incidents/{inc_id}")["incident"]
    return _incident_cache[inc_id]


def fetch() -> list[Item]:
    items: list[Item] = []
    for inc in _paged("/v2/incidents", "incidents", **{"status_category[one_of]": "learning"}):
        _incident_cache[inc["id"]] = inc
        flags = (f"debrief: {'yes' if inc.get('has_debrief') else 'NO'} · "
                 f"postmortem: {'yes' if inc.get('postmortem_document_url') else 'NO'} · "
                 f"{inc['incident_status']['name']}")
        items.append(Item(
            external_id=f"incident:{inc['id']}",
            title=f"{inc['reference']} {inc['name']}"[:200],
            url=inc["permalink"],
            summary=flags,
            data={"kind": "incident", "severity": (inc.get("severity") or {}).get("name"),
                  "has_debrief": inc.get("has_debrief"),
                  "has_postmortem": bool(inc.get("postmortem_document_url"))},
            source_updated_at=inc.get("updated_at", ""),
        ))
    for fu in _paged("/v3/follow_ups", "follow_ups"):
        if fu.get("status") != "outstanding":
            continue
        inc = _incident(fu["incident_id"])
        assignee = (fu.get("assignee") or {}).get("name") or "unassigned"
        items.append(Item(
            external_id=f"followup:{fu['id']}",
            title=f"{inc['reference']} follow-up: {fu['title']}"[:200],
            url=f"{inc['permalink']}/follow-ups",
            summary=f"{assignee} · {(fu.get('priority') or {}).get('name') or 'no priority'}",
            data={"kind": "followup", "assignee": assignee, "incident": inc["reference"]},
            source_updated_at=fu.get("updated_at", ""),
        ))
    return items
