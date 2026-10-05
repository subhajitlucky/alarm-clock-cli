"""Ringing + waiting. Kept separate so it can be unit-tested / mocked."""

from __future__ import annotations

import datetime as dt
import sys
import time

from .timeparse import fmt_countdown


def wait_until(
    trigger: dt.datetime,
    label: str = "",
    tick: float = 1.0,
    sleep_fn=time.sleep,
    now_fn=dt.datetime.now,
    out=None,
) -> None:
    """Block until trigger, printing a live countdown. Ctrl+C cancels cleanly."""
    out = out or sys.stdout
    try:
        while True:
            remaining = (trigger - now_fn()).total_seconds()
            if remaining <= 0:
                break
            out.write(
                f"\r⏳ {label + ' ' if label else ''}in {fmt_countdown(remaining)} "
                f"({trigger.strftime('%H:%M:%S')})  [Ctrl+C cancels] "
            )
            out.flush()
            sleep_fn(min(tick, remaining))
        out.write("\n")
        out.flush()
    except KeyboardInterrupt:
        out.write("\nCancelled — alarm not fired.\n")
        out.flush()
        raise SystemExit(130)


def ring(
    label: str = "Alarm!",
    snooze_default: int = 0,
    input_fn=input,
    out=None,
) -> str:
    """Ring until dismissed. Returns 'dismissed' or 'snoozed:<minutes>'.

    Bell char (\\a) works in most terminals with zero dependencies.
    """
    out = out or sys.stdout
    out.write("\a")  # one immediate bell
    out.write(f"\n🔔 ⏰ {label or 'Alarm!'} — {dt.datetime.now():%H:%M:%S}\n")
    out.flush()
    while True:
        out.write("\a")
        out.flush()
        try:
            choice = input_fn(
                "Press ENTER to dismiss, or 's' to snooze: "
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            out.write("\nDismissed.\n")
            return "dismissed"
        if choice in ("", "d", "dismiss"):
            out.write("Dismissed. Have a good one.\n")
            return "dismissed"
        if choice in ("s", "snooze", "z"):
            mins = snooze_default or 9
            try:
                raw = input_fn(f"Snooze minutes [{mins}]: ").strip()
                if raw:
                    mins = int(raw)
                    if mins <= 0:
                        raise ValueError
            except (ValueError, KeyboardInterrupt, EOFError):
                out.write("Invalid — using default.\n")
                mins = snooze_default or 9
            out.write(f"Snoozed for {mins} min.\n")
            return f"snoozed:{mins}"
        out.write("Type ENTER (dismiss) or 's' (snooze).\n")
