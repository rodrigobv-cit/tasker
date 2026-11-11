# tasker

A local command-line task tracker. No accounts, no server — tasks live in a
`tasks.json` file in the current directory.

## Install

```
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # Windows
# or: .venv/bin/pip install -e ".[dev]"  # macOS/Linux
```

## Usage

```
tasker add "Buy milk"
tasker add "Pay rent" --priority high
tasker list
tasker list --pending
tasker list --done
tasker done 1
tasker edit 1 "Buy oat milk"
tasker priority 1 low
tasker delete 1
tasker session save "Billing spec review" --summary-file notes.md
echo "Piped summary" | tasker session save "Quick note"
```

`--priority` on `add` (and the dedicated `priority <id> <level>` command)
accepts `low`/`normal`/`high`, default `normal`. `list` sorts high before
normal before low, and marks non-normal tasks with a `(high)`/`(low)`
suffix:
```
[ ] #2 Pay rent (high)
[ ] #1 Buy oat milk
[ ] #3 Read a book (low)
```

`session save` writes the summary to
`sessions/<date>-<slug-of-title>.md` (sibling of the tasks file) and adds a
`Resume session: <title> (see sessions/<file>.md)` task in one call. Omit
`--summary-file` to pipe the summary in via stdin instead.

Use `--file path/to/tasks.json` to point at a different storage file. `--file`
must come *before* the subcommand (`tasker --file x.json add ...`), not after.

## Test

```
pytest
```

## Known limitations

- `tasks.json` is stored as `{"next_id": N, "tasks": [...]}`. Older
  `tasks.json` files (a plain list) still load correctly and are migrated to
  this shape the first time anything saves — a one-time, one-way upgrade.
