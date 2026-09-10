"""Sqlite store. One generic items table for every source, one row per sync run."""
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

from scc.config import DATA_DIR

STATUSES = ("new", "watching", "delegated", "ticketed", "done")

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  source TEXT NOT NULL, external_id TEXT NOT NULL,
  title TEXT, url TEXT, summary TEXT, data TEXT,
  first_seen TEXT, last_seen TEXT, source_updated_at TEXT,
  status TEXT DEFAULT 'new', note TEXT DEFAULT '', snoozed_until TEXT,
  PRIMARY KEY (source, external_id)
);
CREATE TABLE IF NOT EXISTS sync_runs (
  source TEXT PRIMARY KEY, ran_at TEXT, ok INTEGER, message TEXT
);
"""


@dataclass
class Item:
    external_id: str
    title: str
    url: str = ""
    summary: str = ""
    data: dict = field(default_factory=dict)
    source_updated_at: str = ""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATA_DIR / "scc.db", isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def upsert_items(source: str, items: list[Item]) -> int:
    ts = now()
    with connect() as conn:
        conn.executemany(
            """INSERT INTO items (source, external_id, title, url, summary, data,
                                  first_seen, last_seen, source_updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(source, external_id) DO UPDATE SET
                 title=excluded.title, url=excluded.url, summary=excluded.summary,
                 data=excluded.data, last_seen=excluded.last_seen,
                 source_updated_at=excluded.source_updated_at""",
            [(source, i.external_id, i.title, i.url, i.summary, json.dumps(i.data),
              ts, ts, i.source_updated_at) for i in items],
        )
    return len(items)


def set_item(source: str, external_id: str, status: str | None = None,
             note: str | None = None, snoozed_until: str | None = None) -> None:
    sets, vals = [], []
    for col, val in (("status", status), ("note", note), ("snoozed_until", snoozed_until)):
        if val is not None:
            sets.append(f"{col}=?")
            vals.append(val)
    if not sets:
        return
    with connect() as conn:
        conn.execute(f"UPDATE items SET {', '.join(sets)} WHERE source=? AND external_id=?",
                     [*vals, source, external_id])


def list_items(source: str, hide_done: bool = True, max_age_hours: int | None = None) -> list[dict]:
    q = "SELECT * FROM items WHERE source=?"
    args: list = [source]
    if hide_done:
        q += " AND status != 'done' AND (snoozed_until IS NULL OR snoozed_until <= ?)"
        args.append(now())
    if max_age_hours is not None:
        q += " AND last_seen >= datetime('now', ?)"
        args.append(f"-{max_age_hours} hours")
    q += " ORDER BY source_updated_at DESC, last_seen DESC"
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(q, args)]
    for r in rows:
        r["data"] = json.loads(r["data"] or "{}")
    return rows


def record_sync(source: str, ok: bool, message: str = "") -> None:
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO sync_runs VALUES (?,?,?,?)",
                     (source, now(), int(ok), message))


def last_syncs() -> dict[str, dict]:
    with connect() as conn:
        return {r["source"]: dict(r) for r in conn.execute("SELECT * FROM sync_runs")}
