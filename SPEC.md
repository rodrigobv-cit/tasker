# Spec: task-tracker CLI

## Objective
A local command-line tool to track personal tasks: add, list, mark done, edit, and delete.
User: a single developer managing a personal to-do list from the terminal. No accounts, no sync, no server.
Success looks like: `tasker add "..."`, `tasker list`, `tasker done <id>`, `tasker edit <id> ...`, `tasker delete <id>` all work against a local JSON file, with tests covering each command.

## Use Cases

1. **Add a task**
   - `tasker add "Buy milk"` → new task created with a unique id, `done=False`; prints `Added #3: Buy milk`.
   - Empty/whitespace-only title → rejected with an error, no task created.
   - Ids are durable: once assigned, an id is never reused, even after the
     task holding it is deleted (a persisted counter, not `max(ids) + 1`).

2. **List tasks**
   - `tasker list` → prints all tasks with id, status (`[ ]`/`[x]`), and title.
   - `tasker list --all` (default) vs `tasker list --pending` vs `tasker list --done` → filtered views.
   - No tasks exist → prints a friendly "no tasks" message, not an error.

3. **Mark a task done**
   - `tasker done 3` → task 3's `done` flips to `True`; prints confirmation.
   - Unknown id → error naming the id, exit code non-zero, no file changes.
   - Already-done task → idempotent (no error, confirms it's already done).

4. **Edit a task's title**
   - `tasker edit 3 "Buy oat milk"` → title updated, id/done untouched.
   - Unknown id → same error behavior as `done`.

5. **Delete a task**
   - `tasker delete 3` → task removed from storage; prints confirmation.
   - Unknown id → error, no file changes.

6. **Save a resumable session**
   - `tasker session save "<title>" --summary-file notes.md` → writes
     `notes.md`'s content to `sessions/<YYYY-MM-DD>-<slug-of-title>.md`
     (sibling directory of the tasks file), then adds a task titled
     `Resume session: <title> (see sessions/<file>.md)`; prints both the
     session file path and the usual `Added #N: ...` confirmation.
   - No `--summary-file` → summary content is read from stdin instead (for
     piping, e.g. from a heredoc or another command's output).
   - Empty/whitespace-only title or summary → rejected with an error, no
     file written and no task created.
   - A session file for that date+title already exists → a numbered suffix
     (`-2`, `-3`, ...) is used instead of overwriting it.
   - `--summary-file` points at a missing/unreadable file → clear error, not
     a stack trace.
   - This is the only command that writes outside `tasks.json`; the
     `sessions/` directory is created on first use if it doesn't exist.

7. **First run / corrupt storage**
   - `tasks.json` doesn't exist yet → treated as an empty task list, created on first write.
   - `tasks.json` exists but is invalid JSON → clear error message, not a stack trace.

## Tech Stack
- Python 3.11+, standard library only (`argparse`, `json`, `dataclasses`, `pathlib`)
- `pytest` for tests (dev dependency only)
- No database, no web framework, no third-party runtime dependencies

## Commands
```
Install (dev):  python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
Run:            python -m tasker <command> ...        (or `tasker ...` once installed)
Test:           python -m pytest
Lint/format:    none configured (kept out of scope for this size of project)
```

## Project Structure
```
task-tracker/
  SPEC.md
  README.md
  pyproject.toml
  src/
    tasker/
      __init__.py
      cli.py          → argparse setup, command dispatch
      storage.py       → load/save tasks.json
      models.py         → Task dataclass
  tests/
    test_storage.py
    test_cli.py
  tasks.json            → created at runtime, gitignored
  sessions/             → created at runtime, gitignored (session summaries)
```

## Code Style
Dataclass for the domain object, small pure functions for storage, argparse subcommands dispatch to plain functions that take parsed args and return printable strings (so they're testable without capturing stdout):

```python
@dataclass
class Task:
    id: int
    title: str
    done: bool = False

def add_task(store: TaskStore, title: str) -> Task:
    task = store.add(title)
    return task
```

- snake_case for functions/variables, PascalCase for classes
- No bare `except:` — catch specific exceptions (e.g. `FileNotFoundError`, `json.JSONDecodeError`)
- Storage path defaults to `./tasks.json` in the current working directory, overridable via `--file`

## Testing Strategy
- `pytest`, tests live in `tests/`
- Unit tests for `storage.py` (load/save/add/complete/delete/edit against a temp file via `tmp_path`)
- Unit tests for `cli.py` command functions (not subprocess — call the dispatch functions directly)
- No coverage threshold enforced, but every command (`add`, `list`, `done`, `edit`, `delete`) must have at least one passing test

## Boundaries
- **Always:** run `pytest` before considering a task done; keep `tasks.json` out of git (`.gitignore`)
- **Ask first:** adding any third-party dependency, changing the storage format in a breaking way
- **Never:** commit `tasks.json` or any other runtime data; push to a remote without being asked

## Success Criteria
- All six commands (`add`, `list`, `done`, `edit`, `delete`, `session save`) implemented and working via `python -m tasker`
- `pytest` passes with tests covering each command
- `README.md` documents installation and usage
- Code is committed to a local git repo with a clean, atomic commit history

## Open Questions
- None — scope is intentionally small and self-contained.
