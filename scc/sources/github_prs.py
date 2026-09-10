"""Open PRs labeled `ops` in the configured repos. Uses the gh CLI so its auth is reused.

Per-repo `gh pr list`, not `gh search prs`: the search index returns incomplete
results under load (seen 2026-09-10: 3 of 4 PRs, incomplete_results=true).
"""
import json
import subprocess

from scc.config import CFG
from scc.db import Item

NAME = "github_prs"
INTERVAL_SECONDS = 900
MAX_AGE_HOURS = 24


def fetch() -> list[Item]:
    items: list[Item] = []
    for repo in CFG["github_repos"]:
        out = subprocess.run(
            ["gh", "pr", "list", "--repo", f"{CFG['github_org']}/{repo}", "--state", "open",
             "--label", CFG["github_label"], "--limit", "100",
             "--json", "number,title,url,author,updatedAt,isDraft,reviewDecision"],
            check=True, capture_output=True, text=True, timeout=60,
        ).stdout
        items += [Item(
            external_id=pr["url"],
            title=f"{repo}#{pr['number']} {pr['title']}"[:200],
            url=pr["url"],
            summary=f"{pr['author']['login']} · {pr.get('reviewDecision') or 'no review'}",
            data={"repo": repo, "author": pr["author"]["login"], "draft": pr["isDraft"],
                  "review": pr.get("reviewDecision")},
            source_updated_at=pr["updatedAt"],
        ) for pr in json.loads(out)]
    return items
