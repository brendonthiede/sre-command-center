"""Notion tasks assigned to me, via a headless `claude -p` run against the Notion MCP connector.

No Notion PAT is available, so Claude does the query. Measured 2026-09-10: ~$0.05/run on Haiku.
The prompt must come before --allowedTools, which is variadic and would swallow it.
"""
import json
import re
import subprocess

from scc.config import CFG
from scc.db import Item

NAME = "notion"
INTERVAL_SECONDS = 3600
MAX_AGE_HOURS = 24 * 3

PROMPT = """Query the Notion database at {url} for tasks assigned to me (the current user) that are not done or completed.
Reply with ONLY a JSON array, no prose, no code fences, one object per task:
[{{"id": "<page id>", "title": "...", "url": "<page url>", "due": "<YYYY-MM-DD or empty>", "status": "<status name>", "updated": "<ISO timestamp>"}}]
If there are no tasks, reply with []."""

TOOLS = ["mcp__claude_ai_Notion__notion-fetch", "mcp__claude_ai_Notion__notion-query-data-sources",
         "mcp__claude_ai_Notion__notion-search", "mcp__claude_ai_Notion__notion-get-users"]


def fetch() -> list[Item]:
    out = subprocess.run(
        ["claude", "-p", PROMPT.format(url=CFG["notion_database_url"]),
         "--model", "claude-haiku-4-5-20251001", "--output-format", "json",
         "--allowedTools", *TOOLS],
        check=True, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL,
    ).stdout
    result = json.loads(out[out.index("{"):])["result"]
    m = re.search(r"\[.*\]", result, re.S)
    if not m:
        raise ValueError(f"no JSON array in claude output: {result[:200]!r}")
    return [Item(
        external_id=t["id"],
        title=t["title"][:200],
        url=t.get("url", ""),
        summary=" · ".join(x for x in (t.get("status"), f"due {t['due']}" if t.get("due") else "") if x),
        data={"due": t.get("due"), "notion_status": t.get("status")},
        source_updated_at=t.get("updated") or "",
    ) for t in json.loads(m.group(0))]
