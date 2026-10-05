"""Pure time-parsing helpers. No I/O, fully testable."""

from __future__ import annotations

import datetime as dt
import re

_DURATION_RE = re.compile(
    r"^\s*(?:(?P<hours>\d+)\s*h)?\s*(?:(?P<minutes>\d+)\s*m)?\s*(?:(?P<seconds>\d+)\s*s)?\s*$",
    re.IGNORECASE,
)


def parse_duration(raw: str) -> int:
    """Parse '10s', '5m', '1h', '1h30m', '90' -> seconds.

    Plain number = seconds. Raises ValueError on bad input or 0.
    """
    raw = raw.strip().lower()
    if re.fullmatch(r"\d+", raw):
        secs = int(raw)
        if secs <= 0:
            raise ValueError("duration must be > 0")
        return secs
    m = _DURATION_RE.fullmatch(raw)
    if not m or not any(m.group(k) for k in ("hours", "minutes", "seconds")):
        raise ValueError(
            f"bad duration {raw!r}; use e.g. '10s', '5m', '1h30m'"
        )
    secs = (
        int(m.group("hours") or 0) * 3600
        + int(m.group("minutes") or 0) * 60
        + int(m.group("seconds") or 0)
    )
    if secs <= 0:
        raise ValueError("duration must be > 0")
    return secs


def parse_time_of_day(raw: str) -> dt.time:
    """Parse '07:30', '7:30:05', '7:30pm', '0730' -> datetime.time.

    Raises ValueError on bad input.
    """
    s = raw.strip().lower().replace(" ", "")
    ampm = None
    if s.endswith("am") or s.endswith("pm"):
        ampm = s[-2:]
        s = s[:-2]

    parts: list[int]
    if ":" in s:
        chunks = s.split(":")
        if len(chunks) not in (2, 3):
            raise ValueError(f"bad time {raw!r}; use HH:MM[:SS]")
        try:
            parts = [int(c) for c in chunks]
        except ValueError:
            raise ValueError(f"bad time {raw!r}; use HH:MM[:SS]")
    elif s.isdigit() and len(s) in (3, 4):
        # 730 -> 07:30, 0730 -> 07:30
        parts = [int(s[:-2]), int(s[-2:])]
    else:
        raise ValueError(f"bad time {raw!r}; use HH:MM[:SS]")

    hour, minute = parts[0], parts[1]
    second = parts[2] if len(parts) == 3 else 0

    if ampm:
        if not 1 <= hour <= 12:
            raise ValueError(f"bad 12h hour in {raw!r}")
        if ampm == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12

    try:
        return dt.time(hour, minute, second)
    except ValueError:
        raise ValueError(f"bad time {raw!r}; out of range")


def next_trigger(target: dt.time, now: dt.datetime | None = None) -> dt.datetime:
    """Next datetime (today or tomorrow) matching target time."""
    now = now or dt.datetime.now()
    candidate = now.replace(
        hour=target.hour,
        minute=target.minute,
        second=target.second,
        microsecond=0,
    )
    if candidate <= now:
        candidate += dt.timedelta(days=1)
    return candidate


def seconds_until(target_dt: dt.datetime, now: dt.datetime | None = None) -> float:
    now = now or dt.datetime.now()
    return max(0.0, (target_dt - now).total_seconds())


def fmt_countdown(total_secs: float) -> str:
    total = int(total_secs)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"
