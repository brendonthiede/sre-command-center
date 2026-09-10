import os
import tempfile

os.environ["SCC_DATA_DIR"] = tempfile.mkdtemp()

from scc import db  # noqa: E402


def test_note_survives_resync():
    db.upsert_items("t", [db.Item("1", "one"), db.Item("2", "two", data={"n": 1})])
    db.set_item("t", "1", status="ticketed", note="filed OPS-1")
    db.upsert_items("t", [db.Item("1", "one renamed")])

    rows = {r["external_id"]: r for r in db.list_items("t", hide_done=False)}
    assert rows["1"]["title"] == "one renamed"
    assert rows["1"]["note"] == "filed OPS-1"
    assert rows["1"]["status"] == "ticketed"
    assert rows["2"]["data"] == {"n": 1}

    db.set_item("t", "2", status="done")
    assert [r["external_id"] for r in db.list_items("t")] == ["1"]

    db.record_sync("t", True, "ok")
    assert db.last_syncs()["t"]["ok"] == 1


if __name__ == "__main__":
    test_note_survives_resync()
    print("ok")
