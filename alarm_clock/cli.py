"""CLI entry point. `python -m alarm_clock --help` for usage."""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from . import __version__
from .ring import ring, wait_until
from .store import Alarm, add, clear, load, next_id, remove, save
from .timeparse import next_trigger, parse_duration, parse_time_of_day


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="alarm-clock",
        description="Minimal CLI alarm clock (stdlib only, no DB).",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("at", help="alarm at a clock time, e.g. at 07:30 -m Standup")
    a.add_argument("time", help="HH:MM[:SS], 12h ('7:30pm') or 4-digit ('0730')")
    a.add_argument("-m", "--message", default="Alarm!", help="label shown on ring")
    a.add_argument("--daily", action="store_true", help="re-arm for same time tomorrow")
    a.add_argument("--snooze", type=int, default=9, help="default snooze minutes")

    t = sub.add_parser("in", help="countdown, e.g. in 10s / in 5m / in 1h30m")
    t.add_argument("duration", help="'10s', '5m', '1h', '1h30m', or seconds")
    t.add_argument("-m", "--message", default="Timer done!", help="label shown on ring")
    t.add_argument("--snooze", type=int, default=5, help="default snooze minutes")

    sub.add_parser("list", help="show pending alarms")
    c = sub.add_parser("cancel", help="cancel a pending alarm by id")
    c.add_argument("id", type=int, help="alarm id from `list`")
    sub.add_parser("clear", help="remove all pending alarms")
    return p


def _fire_with_snooze(message: str, snooze_min: int) -> None:
    while True:
        result = ring(message, snooze_default=snooze_min)
        if result.startswith("snoozed:"):
            mins = int(result.split(":")[1])
            trigger = dt.datetime.now() + dt.timedelta(minutes=mins)
            print(f"Re-armed for {trigger:%H:%M:%S}.")
            wait_until(trigger, label=message)
            continue
        return


def cmd_at(args: argparse.Namespace) -> int:
    try:
        target = parse_time_of_day(args.time)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    trigger = next_trigger(target)
    alarm = Alarm.create(next_id(load()), args.message, trigger, args.daily)
    add(alarm)
    print(f"Alarm #{alarm.id} set for {trigger:%Y-%m-%d %H:%M:%S} — {args.message}")
    try:
        wait_until(trigger, label=args.message)
    except SystemExit as e:
        return int(e.code or 0)
    # fired: drop one-shot, or re-arm daily
    if args.daily:
        alarms = load()
        for a in alarms:
            if a.id == alarm.id:
                nxt = next_trigger(target)
                a.trigger_at = nxt.isoformat(timespec="seconds")
        save(alarms)
        print(f"Daily alarm re-armed for {next_trigger(target):%H:%M:%S} tomorrow.")
    else:
        remove(alarm.id)
    _fire_with_snooze(args.message, args.snooze)
    return 0


def cmd_in(args: argparse.Namespace) -> int:
    try:
        secs = parse_duration(args.duration)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    trigger = dt.datetime.now() + dt.timedelta(seconds=secs)
    alarm = Alarm.create(next_id(load()), args.message, trigger)
    add(alarm)
    print(f"Timer #{alarm.id}: {secs}s → fires at {trigger:%H:%M:%S} — {args.message}")
    try:
        wait_until(trigger, label=args.message)
    except SystemExit as e:
        remove(alarm.id)
        return int(e.code or 0)
    remove(alarm.id)
    _fire_with_snooze(args.message, args.snooze)
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    alarms = sorted(load(), key=lambda a: a.trigger_at)
    if not alarms:
        print("No pending alarms.")
        return 0
    now = dt.datetime.now()
    print(f"{'ID':<4} {'FIRES AT':<19} {'IN':<12} LABEL")
    for a in alarms:
        try:
            t = a.trigger_dt()
            delta = t - now
            left = (
                f"{int(delta.total_seconds() // 3600)}h "
                f"{int(delta.total_seconds() % 3600 // 60):02d}m"
                if delta.total_seconds() > 0
                else "due"
            )
            print(f"{a.id:<4} {t:%Y-%m-%d %H:%M}  {left:<12} {a.label}")
        except ValueError:
            print(f"{a.id:<4} <corrupt date>    {'?':<12} {a.label}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "at":
        return cmd_at(args)
    if args.cmd == "in":
        return cmd_in(args)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "cancel":
        ok = remove(args.id)
        print(f"Cancelled alarm #{args.id}." if ok else f"No alarm #{args.id}.")
        return 0 if ok else 1
    if args.cmd == "clear":
        n = clear()
        print(f"Cleared {n} alarm(s).")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
