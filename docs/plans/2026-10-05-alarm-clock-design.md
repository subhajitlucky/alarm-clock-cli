# Alarm Clock CLI — My Design

Date: 2026-10-05. Timebox: 30 min build. Constraints: CLI only, no web/React/DB.

I wrote this note before coding to fix my scope. Yes — I used AI as allowed to
refine the requirements and plan (details below), but all final decisions are mine.

## How I used AI (my visible thinking)

- Prompt 1: "No spec, 30 min, CLI only — list minimal vs nice-to-have requirements."
  I kept the minimal set, cut audio/TUI/daemon.
- Prompt 2: "Propose 2–3 architectures with trade-offs." AI proposed stdlib CLI /
  pygame / daemon. I chose #1 for reviewability.
- Prompt 3: "Draft an implementation plan + module split." I approved
  timeparse → store → ring → cli, then had it draft per-module and I reviewed
  every file before testing.

## My requirements (from "no spec")

Must: `at HH:MM` alarm, `in <duration>` timer, `list`/`cancel`/`clear`,
ring with message + dismiss/snooze, input validation, Ctrl+C-safe.
Should: daily repeat, 12h + 4-digit time formats, file persistence across terminals.
Won't (30-min cut): audio files, TUI, daemon, tz flags, notifications.

## Approaches I considered

1. **Single-purpose stdlib CLI (my choice).** Zero deps, ~400 lines, fully
   testable. Risk: plain bell instead of rich audio — I accepted this trade-off
   and documented it.
2. Rich + pygame audio. Nicer sound, but install friction + untestable in 30 min,
   so I rejected it.
3. Daemon + scheduler. Proper for "real" alarms, but I rejected it as
   un-demoable and un-reviewable in the timebox.

## My architecture

`timeparse.py` (pure) → `store.py` (atomic JSON) → `ring.py` (wait/ring) →
`cli.py` (argparse only). Dependency rule: CLI depends on all, nobody depends
on CLI. Parsing and ringing take injectable `now_fn`/`sleep_fn`/`input_fn` so
tests never sleep or block.

## My error handling

Bad time/duration → stderr + exit 2. Corrupt JSON rows skipped, `list` never
crashes. Missing file → empty list. Ctrl+C while waiting → "Cancelled", exit
130, pending entry removed. Snooze input invalid → fall back to default.

## My validation

33 pytest cases (parsing table-tests, store round-trip, ring dismiss/snooze
with mocked input). Manual: `in 2s` fire/dismiss, `list` empty after, bad
inputs checked. Result: 33 passed, manual fire confirmed.
