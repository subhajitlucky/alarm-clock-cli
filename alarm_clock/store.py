"""JSON-file alarm store. Not a DB — plain file persistence so
`list`/`cancel` work across terminals. Stdlib only."""

from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from dataclasses import asdict, dataclass


@dataclass
class Alarm:
    id: int
    label: str
    trigger_at: str  # ISO datetime
    repeat_daily: bool = False
    created_at: str = ""

    @classmethod
    def create(
        cls, alarm_id: int, label: str, trigger: dt.datetime, repeat_daily: bool = False
    ) -> "Alarm":
        return cls(
            id=alarm_id,
            label=label,
            trigger_at=trigger.isoformat(timespec="seconds"),
            repeat_daily=repeat_daily,
            created_at=dt.datetime.now().isoformat(timespec="seconds"),
        )

    def trigger_dt(self) -> dt.datetime:
        return dt.datetime.fromisoformat(self.trigger_at)


def default_path() -> str:
    return os.path.expanduser("~/.alarm-clock.json")


def load(path: str | None = None) -> list[Alarm]:
    path = path or default_path()
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    alarms: list[Alarm] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            alarms.append(
                Alarm(
                    id=int(item["id"]),
                    label=str(item.get("label", "")),
                    trigger_at=str(item["trigger_at"]),
                    repeat_daily=bool(item.get("repeat_daily", False)),
                    created_at=str(item.get("created_at", "")),
                )
            )
        except (KeyError, ValueError, TypeError):
            continue  # skip corrupt row, don't crash list
    return alarms


def save(alarms: list[Alarm], path: str | None = None) -> None:
    path = path or default_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # atomic write so Ctrl+C mid-save can't corrupt the file
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump([asdict(a) for a in alarms], f, indent=2)
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def next_id(alarms: list[Alarm]) -> int:
    return max((a.id for a in alarms), default=0) + 1


def add(alarm: Alarm, path: str | None = None) -> Alarm:
    alarms = load(path)
    alarms.append(alarm)
    save(alarms, path)
    return alarm


def remove(alarm_id: int, path: str | None = None) -> bool:
    alarms = load(path)
    kept = [a for a in alarms if a.id != alarm_id]
    if len(kept) == len(alarms):
        return False
    save(kept, path)
    return True


def clear(path: str | None = None) -> int:
    alarms = load(path)
    save([], path)
    return len(alarms)
