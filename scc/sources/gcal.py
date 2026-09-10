"""Events in the next 48h across every selected calendar of the Google account.

One-time setup: credentials.json (Desktop OAuth client) in the repo root; first run opens a
browser for consent and writes token.json. Share work calendars into this account.
"""
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from scc.config import ROOT
from scc.db import Item

NAME = "gcal"
INTERVAL_SECONDS = 600
MAX_AGE_HOURS = 2
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _creds() -> Credentials:
    token = ROOT / "token.json"
    creds = Credentials.from_authorized_user_file(token, SCOPES) if token.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        creds = InstalledAppFlow.from_client_secrets_file(ROOT / "credentials.json", SCOPES).run_local_server(port=0)
    token.write_text(creds.to_json())
    return creds


def fetch() -> list[Item]:
    svc = build("calendar", "v3", credentials=_creds(), cache_discovery=False)
    now = datetime.now(timezone.utc)
    day_start = now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    items: list[Item] = []
    for cal in svc.calendarList().list().execute().get("items", []):
        if not cal.get("selected", True):
            continue
        events = svc.events().list(calendarId=cal["id"], timeMin=day_start.isoformat(),
                                   timeMax=(now + timedelta(hours=48)).isoformat(),
                                   singleEvents=True, orderBy="startTime", maxResults=50).execute()
        for ev in events.get("items", []):
            if ev.get("status") == "cancelled":
                continue
            start = ev["start"].get("dateTime") or ev["start"].get("date")
            end = ev["end"].get("dateTime") or ev["end"].get("date")
            items.append(Item(
                external_id=f"{cal['id']}:{ev['id']}",
                title=ev.get("summary", "(no title)")[:200],
                url=ev.get("htmlLink", ""),
                summary=cal.get("summaryOverride") or cal.get("summary", ""),
                data={"start": start, "end": end, "all_day": "date" in ev["start"],
                      "calendar": cal.get("summary"), "attendees": len(ev.get("attendees", []))},
                source_updated_at=start,
            ))
    items.sort(key=lambda i: i.data["start"])
    return items
