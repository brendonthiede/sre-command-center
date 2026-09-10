"""Top-level messages in the team support channel from the last 7 days.

Needs a Slack user token with channels:history + channels:read (groups:* if private).
"""
import time

import requests

from scc.config import CFG, secret
from scc.db import Item

NAME = "slack_support"
INTERVAL_SECONDS = 300
MAX_AGE_HOURS = 24 * 7
_team_url: str = ""


def _call(method: str, **params) -> dict:
    r = requests.get(f"https://slack.com/api/{method}", params=params, timeout=30,
                     headers={"Authorization": f"Bearer {secret('SLACK_USER_TOKEN')}"})
    r.raise_for_status()
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(f"slack {method}: {body.get('error')}")
    return body


def fetch() -> list[Item]:
    global _team_url
    if not _team_url:
        _team_url = _call("auth.test")["url"].rstrip("/")
    ch = CFG["slack_support_channel"]
    # int: Slack returns an empty list for `oldest` with >6 decimals, no error (seen 2026-09-10)
    oldest = int(time.time() - MAX_AGE_HOURS * 3600)
    items: list[Item] = []
    cursor = None
    while True:
        body = _call("conversations.history", channel=ch, oldest=oldest, limit=200,
                     **({"cursor": cursor} if cursor else {}))
        for m in body["messages"]:
            if m.get("subtype") in ("channel_join", "channel_leave", "bot_add"):
                continue
            text = (m.get("text") or "").replace("\n", " ").strip()
            author = (m.get("user_profile") or {}).get("real_name") or m.get("username") or m.get("user", "?")
            items.append(Item(
                external_id=m["ts"],
                title=text[:160] or "(no text)",
                url=f"{_team_url}/archives/{ch}/p{m['ts'].replace('.', '')}",
                summary=f"{author} · {m.get('reply_count', 0)} replies",
                data={"author": author, "reply_count": m.get("reply_count", 0),
                      "latest_reply": m.get("latest_reply")},
                source_updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                time.gmtime(float(m.get("latest_reply") or m["ts"]))),
            ))
        cursor = (body.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            return items
