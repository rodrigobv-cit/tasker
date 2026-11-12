# tasker

A local, single-user CLI task tracker. No accounts, no server — see `SPEC.md`
for the full spec and `tasks/plan.md` for the feature/task breakdown and
history of what's shipped.

## Tech Stack
- Python 3.11+, standard library only (`argparse`, `json`, `dataclasses`, `pathlib`, `datetime`).
- `pytest` for tests — a dev dependency only.
- No database, no web framework, no third-party runtime dependencies. Adding
  one is an "ask first" boundary (see below), not a default move.

## Commands
```
Install (dev):  python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
Run:            python -m tasker <command> ...        (or `tasker ...` once installed)
Test:           python -m pytest
Lint/format:    none configured (kept out of scope for this size of project)
```

## Project Structure
```
src/tasker/
  cli.py       → argparse setup, command dispatch, all command logic
  storage.py   → TaskStore: load/save tasks.json
  models.py    → Task dataclass, priority constants
tests/
  test_storage.py
  test_cli.py
tasks.json     → created at runtime, gitignored
sessions/      → created at runtime, gitignored (resumable session summaries)
```

## Code Style
- Dataclass for the domain object (`Task`), small pure functions for storage.
- CLI command functions take parsed args + a `TaskStore` and return a string
  to print — testable by calling them directly, no subprocess/stdout capture.
- snake_case functions/variables, PascalCase classes.
- No bare `except:` — catch specific exceptions (`FileNotFoundError`,
  `json.JSONDecodeError`, etc.).
- `--file` is a top-level argparse option and **must come before** the
  subcommand (`tasker --file x.json add ...`, not `tasker add ... --file
  x.json`) — easy to get backwards.

## Testing
- `pytest`, tests in `tests/`. Every command needs at least one passing test.
- Where a function's output depends on the current time (e.g. `session
  save`'s embedded timestamp), monkeypatch `tasker.cli._now` for determinism
  rather than asserting against the real clock.

## Boundaries
- **Always:** run `pytest` before considering a task done.
- **Ask first:** adding a third-party dependency; changing the `tasks.json`
  storage format in a breaking way.
- **Never:** commit `tasks.json`, `tasks.json.bak`, or anything under
  `sessions/` (all gitignored — personal runtime data); push to the remote
  without being asked first, even after a commit is approved.
