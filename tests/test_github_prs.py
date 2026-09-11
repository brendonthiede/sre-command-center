from scc.sources.github_prs import _wanted


def test_wanted():
    labeled = {"labels": [{"name": "ops"}], "reviewRequests": []}
    team = {"labels": [{"name": "billing"}],
            "reviewRequests": [{"__typename": "Team", "slug": "orgname/ops"}]}
    user = {"labels": [{"name": "billing"}],
            "reviewRequests": [{"__typename": "User", "login": "ops"}]}
    assert _wanted(labeled, "ops", "orgname/ops")
    assert _wanted(team, "ops", "orgname/ops")
    assert not _wanted(user, "ops", "orgname/ops")
