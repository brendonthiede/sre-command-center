"""Consistent sqlite copy, then scp to the NAS if nas_target is set.

`scp -O` (legacy protocol): the Synology has neither the rsync service nor the SFTP
subsystem enabled for this user, and the legacy protocol needs only a shell.
"""
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
    subprocess.run(["scp", "-O", "-q", "-o", "BatchMode=yes", str(dst), target], check=True, timeout=300)
    return f"wrote {dst} and copied to {target}"
