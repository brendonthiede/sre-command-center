import logging

from scc import db
from scc.sources import BY_NAME

log = logging.getLogger("scc.sync")


def sync_source(name: str) -> int:
    src = BY_NAME[name]
    try:
        items = src.fetch()
    except Exception as e:  # record and re-raise so CLI shows it, scheduler swallows it
        db.record_sync(name, False, f"{type(e).__name__}: {e}"[:500])
        raise
    n = db.upsert_items(name, items)
    db.record_sync(name, True, f"{n} items")
    return n
