# Alarm Clock CLI

Minimal Python CLI alarm clock. Stdlib only, no web UI, no database.

Built by me as a 30-minute build exercise — I kept the scope deliberately
small so the whole thing is reviewable, testable, and demoable in one recording.

## How I built it — with AI (as the brief requires)

Yes, I used AI throughout, as allowed. My process:

1. **I asked AI to refine requirements:** from "alarm clock, no spec" I had it
   list options, then I fixed the scope myself: two ways to set
   (`at HH:MM` + `in 10s/5m/1h`), `list`/`cancel`/`clear`, snooze + dismiss,
   daily repeat. I rejected audio files, TUI, and daemon mode — too much for
   30 min and dependency risk.
2. **I asked AI to propose designs:** it gave 3 approaches (stdlib CLI vs
   Rich/pygame vs daemon). I chose stdlib-only: pure parse helpers
   (`timeparse.py`) so the tricky logic is unit-testable without sleeping;
   thin `store.py` (atomic JSON file, not a DB); `ring.py` for wait/ring;
   `cli.py` only wires argparse.
3. **I directed, reviewed, and validated:** AI drafted per-module, I reviewed
   every line, ran `pytest` (33 tests), plus manual `in 2s` fire/dismiss and
   bad-input checks (`25:00`, `0s`). I found and fixed one wiring bug during
   review. Final decisions and testing were mine.

## Install

Python 3.9+. No dependencies.

```bash
git clone <your-repo-url> alarm-clock-cli
cd alarm-clock-cli
python3 -m alarm_clock --help
# optional isolated test env:
python3 -m venv .venv && .venv/bin/pip install pytest && .venv/bin/python -m pytest -q
```

Or install as a command:

```bash
pip install -e .
alarm-clock --help
```

## Usage

```bash
# alarm at a clock time (24h, 12h, or 4-digit all work)
python3 -m alarm_clock at 07:30 -m "Standup"
python3 -m alarm_clock at 7:30pm -m "Gym" --daily

# countdown timer
python3 -m alarm_clock in 10s -m "Tea"
python3 -m alarm_clock in 25m -m "Pomodoro"
python3 -m alarm_clock in 1h30m -m "Deep work"

# manage
python3 -m alarm_clock list
python3 -m alarm_clock cancel 2
python3 -m alarm_clock clear
```

On ring: terminal bell + message. `ENTER` dismisses, `s` snoozes
(default 9 min for `at`, 5 min for `in`). `Ctrl+C` while waiting cancels cleanly.
Pending alarms live in `~/.alarm-clock.json` (plain file, not a DB) so `list`
works from another terminal.

## My design decisions

| Decision | My reasoning |
|---|---|
| Stdlib only, zero deps | Reviewer can run it with one command; no audio-lib install risk in 30 min |
| Pure `timeparse.py` | Duration/clock parsing is the bug-prone core — isolated for 20+ unit tests, no sleeps |
| Atomic JSON file, corrupt-row tolerant | `list` must never crash; `os.replace` write avoids half-written files on Ctrl+C |
| Blocking wait + live countdown | Simplest demoable behavior; a daemon/cron would be un-reviewable in 30 min |
| Bell char (`\a`) not pygame | Cross-platform beep with no assets; documented as the conscious trade-off |
| Daily = re-arm same HH:MM | Avoids scheduler complexity; explicit and testable |

Out of scope by my call: real audio files, multiple concurrent ringing,
system notifications, timezone flags. Each would double the review surface.

## Tests

```bash
python3 -m pytest -q   # 33 tests: parsing, store round-trip, ring/wait (mocked I/O)
```

Also validated by me manually: `in 2s` fires + dismisses, `list` empty after fire,
bad inputs exit 2 with a message.

## Layout

```
alarm_clock/__init__.py  version
alarm_clock/timeparse.py pure parsing (parse_duration, parse_time_of_day, next_trigger)
alarm_clock/store.py     JSON-file CRUD (load/save/add/remove/clear)
alarm_clock/ring.py      wait_until countdown + ring/snooze loop
alarm_clock/cli.py       argparse wiring only
tests/                   test_timeparse.py, test_store_ring.py
docs/plans/              my design note from before coding
```

## Demo script (for the screen recording, ~2 min)

1. `python3 -m alarm_clock --help` — show the 5 commands.
2. `python3 -m alarm_clock in 5s -m "Demo"` — narrate the countdown, dismiss with ENTER.
3. `python3 -m alarm_clock at 99:99` — show the validation error.
4. `python3 -m pytest -q` — 33 passed.
