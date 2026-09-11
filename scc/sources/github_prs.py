"""Open PRs in the configured repos that are labeled `ops` or have the ops team as a
reviewer. Uses the gh CLI so its auth is reused.

Per-repo `gh pr list`, not `gh search prs`: the search index returns incomplete
results under load (seen 2026-09-10: 3 of 4 PRs, incomplete_results=true).
Label and reviewer are OR'd, which `gh pr list --label` cannot express, so both
are filtered client-side.
"""
import json
import subprocess

from scc.config import CFG
from scc.db import Item

NAME = "github_prs"
INTERVAL_SECONDS = 900
MAX_AGE_HOURS = 24


def _wanted(pr: dict, label: str, team: str) -> bool:
    return (any(l["name"] == label for l in pr["labels"])
            # team review requests carry `slug` as "org/team"; user ones have `login` instead
            or any(r.get("slug") == team for r in pr["reviewRequests"]))


def fetch() -> list[Item]:
    label, team = CFG["github_label"], CFG.get("github_review_team", "")
    items: list[Item] = []
    for repo in CFG["github_repos"]:
        out = subprocess.run(
            ["gh", "pr", "list", "--repo", f"{CFG['github_org']}/{repo}", "--state", "open",
             "--limit", "100", "--json",
             "number,title,url,author,updatedAt,isDraft,reviewDecision,labels,reviewRequests"],
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
        ) for pr in json.loads(out) if _wanted(pr, label, team)]
    return items
