# Task List: task-tracker CLI

## Feature 1: Storage foundation (Use Case 6)

### Task 1.1: Scaffold package + Task dataclass
**Description:** Create the package skeleton and the `Task` dataclass.
**Acceptance criteria:**
- [x] `pyproject.toml` defines the `tasker` package and a `pytest` dev dependency
- [x] `src/tasker/models.py` defines `Task(id: int, title: str, done: bool = False)`
**Verification:**
- [x] `python -c "from tasker.models import Task"` succeeds after `pip install -e .`
**Dependencies:** None
**Files likely touched:** `pyproject.toml`, `src/tasker/__init__.py`, `src/tasker/models.py`
**Estimated scope:** XS (2 files)

### Task 1.2: TaskStore load/save with first-run and corrupt-file handling
**Description:** Implement `storage.py` with `TaskStore.load`, `.save`, `.add`, `.get`, `.all`, backed by a JSON file path.
**Acceptance criteria:**
- [x] Missing file → `TaskStore.load` returns an empty store (no error)
- [x] Invalid JSON → raises a `TaskStoreError` with a clear message (no raw traceback surfaced to the CLI)
- [x] `save` writes valid JSON that `load` can read back byte-for-byte equivalent
**Verification:**
- [x] `pytest tests/test_storage.py`
**Dependencies:** Task 1.1
**Files likely touched:** `src/tasker/storage.py`, `tests/test_storage.py`
**Estimated scope:** S (2 files)

## Checkpoint: Feature 1 complete
- [x] `pytest tests/test_storage.py` passes
- [x] Manual check: delete `tasks.json`, run anything → no crash; write garbage into `tasks.json` → clear error

## Feature 2: Add a task (Use Case 1)

### Task 2.1: add command
**Description:** Implement `add_task(store, title)` and wire the `add` CLI subcommand.
**Acceptance criteria:**
- [x] `tasker add "Buy milk"` creates a task with a unique id, `done=False`, prints `Added #<id>: <title>`
- [x] Empty/whitespace title → rejected with a non-zero exit and an error message, no task created
**Verification:**
- [x] `pytest tests/test_cli.py -k add`
**Dependencies:** Feature 1
**Files likely touched:** `src/tasker/cli.py`, `tests/test_cli.py`
**Estimated scope:** S (2 files)

## Feature 3: List tasks (Use Case 2)

### Task 3.1: list command
**Description:** Implement `list_tasks(store, filter)` and wire the `list` CLI subcommand with `--all`/`--pending`/`--done`.
**Acceptance criteria:**
- [x] `tasker list` prints every task with id, `[ ]`/`[x]`, and title
- [x] `--pending` / `--done` filter correctly
- [x] No tasks → friendly "no tasks" message, not an error
**Verification:**
- [x] `pytest tests/test_cli.py -k list`
**Dependencies:** Feature 1 (can run parallel to Feature 2 — no shared state beyond the store)
**Files likely touched:** `src/tasker/cli.py`, `tests/test_cli.py`
**Estimated scope:** S (2 files)

## Feature 4: Mark a task done (Use Case 3)

### Task 4.1: done command
**Description:** Implement `complete_task(store, id)` and wire the `done` CLI subcommand.
**Acceptance criteria:**
- [x] `tasker done <id>` sets `done=True`, prints confirmation
- [x] Unknown id → error naming the id, non-zero exit, no file changes
- [x] Already-done task → idempotent, no error, confirms already done
**Verification:**
- [x] `pytest tests/test_cli.py -k done`
**Dependencies:** Feature 2 (needs a task to mark done in tests)
**Files likely touched:** `src/tasker/cli.py`, `tests/test_cli.py`
**Estimated scope:** S (2 files)

## Feature 5: Edit a task's title (Use Case 4)

### Task 5.1: edit command
**Description:** Implement `edit_task(store, id, title)` and wire the `edit` CLI subcommand.
**Acceptance criteria:**
- [x] `tasker edit <id> "new title"` updates title only, id/done untouched
- [x] Unknown id → same error behavior as `done`
**Verification:**
- [x] `pytest tests/test_cli.py -k edit`
**Dependencies:** Feature 2
**Files likely touched:** `src/tasker/cli.py`, `tests/test_cli.py`
**Estimated scope:** S (2 files)

## Feature 6: Delete a task (Use Case 5)

### Task 6.1: delete command
**Description:** Implement `delete_task(store, id)` and wire the `delete` CLI subcommand.
**Acceptance criteria:**
- [x] `tasker delete <id>` removes the task, prints confirmation
- [x] Unknown id → error, non-zero exit, no file changes
**Verification:**
- [x] `pytest tests/test_cli.py -k delete`
**Dependencies:** Feature 2
**Files likely touched:** `src/tasker/cli.py`, `tests/test_cli.py`
**Estimated scope:** S (2 files)

## Checkpoint: Complete
- [x] `pytest` passes (all tests, every command covered)
- [x] `README.md` written
- [x] One git commit per Feature, clean history
- [x] Ready for code review
