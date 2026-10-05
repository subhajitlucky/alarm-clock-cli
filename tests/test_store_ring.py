import datetime as dt

from alarm_clock import store
from alarm_clock.ring import ring, wait_until


def test_store_add_remove_roundtrip(tmp_path):
    path = str(tmp_path / "alarms.json")
    a = store.Alarm.create(1, "test", dt.datetime(2026, 1, 1, 7, 30))
    store.add(a, path)
    assert len(store.load(path)) == 1
    assert store.remove(1, path) is True
    assert store.load(path) == []
    assert store.remove(999, path) is False


def test_store_skips_corrupt_rows(tmp_path):
    path = str(tmp_path / "alarms.json")
    with open(path, "w") as f:
        f.write('[{"id": 1, "label": "ok", "trigger_at": "2026-01-01T07:30:00"}, {"bad": 1}]')
    assert len(store.load(path)) == 1


def test_wait_until_fires_immediately_for_past_time(capsys):
    past = dt.datetime.now() - dt.timedelta(seconds=5)
    wait_until(past, sleep_fn=lambda s: None)
    assert capsys.readouterr().out is not None


def test_ring_dismiss_on_enter():
    assert ring("hi", input_fn=lambda _: "") == "dismissed"


def test_ring_snooze_returns_minutes():
    answers = iter(["s", "10"])
    assert ring("hi", input_fn=lambda _: next(answers)) == "snoozed:10"
