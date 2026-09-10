"""Flask dashboard plus the background sync thread."""
import logging
import threading
import time
from datetime import datetime, timezone

from flask import Flask, redirect, render_template, request

from scc import db
from scc.backup import backup
from scc.config import CFG
from scc.sources import BY_NAME, SOURCES
from scc.sync import sync_source

log = logging.getLogger("scc.web")
app = Flask(__name__)


def _age(iso: str | None) -> str:
    if not iso:
        return "never"
    t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    s = int((datetime.now(timezone.utc) - t).total_seconds())
    if s < 90:
        return f"{s}s"
    if s < 5400:
        return f"{s // 60}m"
    if s < 172800:
        return f"{s // 3600}h"
    return f"{s // 86400}d"


app.jinja_env.filters["age"] = _age


@app.get("/")
def index():
    syncs = db.last_syncs()
    sections = []
    for s in SOURCES:
        rows = db.list_items(s.NAME, max_age_hours=s.MAX_AGE_HOURS)
        if s.NAME == "gcal":  # soonest first; everything else is newest first
            rows.sort(key=lambda r: r["data"]["start"])
        sections.append({"name": s.NAME, "rows": rows, "sync": syncs.get(s.NAME)})
    return render_template("index.html", sections=sections, statuses=db.STATUSES)


@app.post("/item/<source>/<path:external_id>")
def update_item(source, external_id):
    f = request.form
    db.set_item(source, external_id, status=f.get("status"), note=f.get("note"),
                snoozed_until=f.get("snoozed_until") or "")
    return redirect(f"/#{source}")


@app.post("/sync/<source>")
def sync_now(source):
    try:
        sync_source(source)
    except Exception:
        log.exception("sync %s failed", source)
    return redirect(f"/#{source}")


def _scheduler() -> None:
    last: dict[str, float] = {"backup": time.monotonic()}
    while True:
        if time.monotonic() - last["backup"] >= 86400:
            last["backup"] = time.monotonic()
            try:
                log.info(backup())
            except Exception as e:
                log.warning("backup failed: %s", e)
        for s in SOURCES:
            if time.monotonic() - last.get(s.NAME, -1e9) < s.INTERVAL_SECONDS:
                continue
            last[s.NAME] = time.monotonic()
            try:
                n = sync_source(s.NAME)
                log.info("synced %s: %d items", s.NAME, n)
            except Exception as e:
                log.warning("sync %s failed: %s", s.NAME, e)
        time.sleep(30)


def serve() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    threading.Thread(target=_scheduler, daemon=True).start()
    app.run(host="127.0.0.1", port=CFG["port"], debug=False)
