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
tasker list
tasker list --pending
tasker list --done
tasker done 1
tasker edit 1 "Buy oat milk"
tasker delete 1
```

Use `--file path/to/tasks.json` to point at a different storage file. `--file`
must come *before* the subcommand (`tasker --file x.json add ...`), not after.

## Test

```
pytest
```

## Known limitations

- Task ids are the highest id in the file + 1 at load time, not a persisted
  counter. Deleting the highest-numbered task and then adding a new one will
  reuse that id. Fine for a single-user scratch list; don't rely on an id as
  a permanent reference.
