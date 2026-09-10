"""Config: secrets from .env (into os.environ), settings from config.toml.

Falls back to config.example.toml so a fresh clone runs with placeholders.
"""
import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("SCC_DATA_DIR", ROOT / "data"))


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")

_cfg_path = ROOT / "config.toml"
if not _cfg_path.exists():
    _cfg_path = ROOT / "config.example.toml"
CFG: dict = tomllib.loads(_cfg_path.read_text())


def secret(name: str) -> str:
    """Return a required env var or raise with a message naming it."""
    v = os.environ.get(name)
    if not v:
        raise KeyError(f"{name} is not set; add it to .env")
    return v
