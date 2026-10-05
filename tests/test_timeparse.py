import datetime as dt

import pytest

from alarm_clock.timeparse import (
    fmt_countdown,
    next_trigger,
    parse_duration,
    parse_time_of_day,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("10", 10),
        ("10s", 10),
        ("5m", 300),
        ("2h", 7200),
        ("1h30m", 5400),
        ("1H 5M 10S", 3910),
    ],
)
def test_parse_duration_ok(raw, expected):
    assert parse_duration(raw) == expected


@pytest.mark.parametrize("raw", ["", "0", "0s", "abc", "1x", "m", "--5"])
def test_parse_duration_bad(raw):
    with pytest.raises(ValueError):
        parse_duration(raw)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("07:30", (7, 30, 0)),
        ("7:30:05", (7, 30, 5)),
        ("23:59:59", (23, 59, 59)),
        ("7:30pm", (19, 30, 0)),
        ("12:00am", (0, 0, 0)),
        ("12:00pm", (12, 0, 0)),
        ("0730", (7, 30, 0)),
    ],
)
def test_parse_time_ok(raw, expected):
    t = parse_time_of_day(raw)
    assert (t.hour, t.minute, t.second) == expected


@pytest.mark.parametrize("raw", ["", "25:00", "12:60", "abc", "7pmx", "12345"])
def test_parse_time_bad(raw):
    with pytest.raises(ValueError):
        parse_time_of_day(raw)


def test_next_trigger_rolls_to_tomorrow():
    now = dt.datetime(2026, 1, 1, 8, 0, 0)
    assert next_trigger(dt.time(7, 0), now) == dt.datetime(2026, 1, 2, 7, 0, 0)
    assert next_trigger(dt.time(9, 0), now) == dt.datetime(2026, 1, 1, 9, 0, 0)


def test_fmt_countdown():
    assert fmt_countdown(5) == "5s"
    assert fmt_countdown(90) == "1m 30s"
    assert fmt_countdown(3700) == "1h 01m 40s"
