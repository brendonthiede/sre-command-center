from scc.sources.github_prs import _wanted


def test_wanted():
    labeled = {"labels": [{"name": "ops"}], "reviewRequests": [], "author": {"login": "someone"}, "assignees": []}
    team = {"labels": [{"name": "billing"}],
            "reviewRequests": [{"__typename": "Team", "slug": "orgname/ops"}], "author": {"login": "someone"}, "assignees": []}
    user = {"labels": [{"name": "billing"}],
            "reviewRequests": [{"__typename": "User", "login": "ops"}], "author": {"login": "someone"}, "assignees": []}
    mine = {**user, "author": {"login": "me"}}
    assigned = {**user, "assignees": [{"login": "me"}]}
    assert _wanted(labeled, "ops", "orgname/ops", "me")
    assert _wanted(team, "ops", "orgname/ops", "me")
    assert not _wanted(user, "ops", "orgname/ops", "me")
    assert _wanted(mine, "ops", "orgname/ops", "me")
    assert _wanted(assigned, "ops", "orgname/ops", "me")
