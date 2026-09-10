"""Consistent sqlite copy, then rsync to the NAS if nas_target is set."""
import sqlite3
import subprocess

from scc.config import CFG, DATA_DIR


def backup() -> str:
    src = DATA_DIR / "scc.db"
    dst = DATA_DIR / "scc-backup.db"
    with sqlite3.connect(src) as a, sqlite3.connect(dst) as b:
        a.backup(b)
    target = CFG.get("nas_target")
    if not target:
        return f"wrote {dst}; nas_target not set, skipped rsync"
    subprocess.run(["rsync", "-a", str(dst), target], check=True, timeout=300)
    return f"wrote {dst} and rsynced to {target}"
