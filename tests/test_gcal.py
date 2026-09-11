from scc.config import CFG
from scc.sources import gcal

CALS = [
    {"id": "brendon@randomdomainname.com", "summary": "Brendon", "selected": True},
    {"id": "abc123@group.calendar.google.com", "summary": "SRE On-Call", "selected": False},
    {"id": "holidays@group.v.calendar.google.com", "summary": "Holidays in US", "selected": True},
]


def test_filter_falls_back_to_selected():
    CFG.pop("gcal_calendars", None)
    assert [c["id"] for c in CALS if gcal._wanted(c)] == [CALS[0]["id"], CALS[2]["id"]]


def test_named_calendars_win_over_selected():
    CFG["gcal_calendars"] = ["on-call", "brendon@randomdomainname.com"]
    try:
        assert [c["summary"] for c in CALS if gcal._wanted(c)] == ["Brendon", "SRE On-Call"]
    finally:
        CFG.pop("gcal_calendars")
