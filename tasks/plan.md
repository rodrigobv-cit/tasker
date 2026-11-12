# Implementation Plan: task-tracker CLI

## Overview
A stdlib-only Python CLI for tracking personal tasks against a local JSON file. Six Use Cases from SPEC.md, each implemented as one Feature. No frontend exists for this project (it's a terminal tool), so the usual backend/frontend vertical slice does not apply — each Feature's "slice" is instead: storage logic + CLI command + tests, which is the full vertical for a CLI app.

## Architecture Decisions
- **Foundation first:** Use Case 6 (storage/first-run/corrupt-file handling) underlies every other command, so it's built as Feature 1 before any command exists. Every later Feature depends on it.
- **Testable-by-function, not subprocess:** CLI command functions take parsed args + a `TaskStore` and return a string to print, so tests call them directly instead of spawning subprocesses.
- **No ORM/DB:** `tasks.json` read/written wholesale on every command — appropriate at this scale, avoids premature complexity.

## Features List and Task List

### Feature 1: Storage foundation (Use Case 6)
- [ ] Task 1.1: Scaffold package + `Task` dataclass
- [ ] Task 1.2: `TaskStore` load/save, with empty-file and corrupt-JSON handling

### Checkpoint: Feature 1 complete
- [ ] `pytest tests/test_storage.py` passes
- [ ] Manually confirm: missing `tasks.json` → empty store; invalid JSON → clear error, not a traceback

### Feature 2: Add a task (Use Case 1)
- [ ] Task 2.1: `add_task` function + `add` CLI subcommand + tests

### Feature 3: List tasks (Use Case 2)
- [ ] Task 3.1: `list_tasks` function (with `--all`/`--pending`/`--done` filters) + `list` CLI subcommand + tests

### Feature 4: Mark a task done (Use Case 3)
- [ ] Task 4.1: `complete_task` function + `done` CLI subcommand + tests (incl. unknown id, already-done)

### Feature 5: Edit a task's title (Use Case 4)
- [ ] Task 5.1: `edit_task` function + `edit` CLI subcommand + tests (incl. unknown id)

### Feature 6: Delete a task (Use Case 5)
- [ ] Task 6.1: `delete_task` function + `delete` CLI subcommand + tests (incl. unknown id)

### Checkpoint: Feature 6 complete
- [ ] `pytest` passes end-to-end
- [ ] README.md documents install + usage
- [ ] `git log` shows one commit per Feature

### Feature 7: Save a resumable session (Use Case 6)
Added after the original six Features shipped, to replace the manual
two-step "write a file, then hand-craft a task title" process (model-driven,
per `~/.claude/skills/tasker/SKILL.md`) with one atomic CLI command plus a
slash command that triggers it. Additive only: no changes to the `Task`
dataclass or the `tasks.json` shape, no id-reuse fix, no timestamps/priority/
due-dates — those stay deferred (see `sessions/2026-11-10-tasker-improvements.md`).
- [x] Task 7.1: `save_session` function (slugify title, date-stamped
      filename with numbered-suffix collision handling, write summary file,
      create linked task, save) + nested `session save` CLI subcommand
      (`--summary-file` or stdin) + tests in `tests/test_cli.py` (happy path
      via file, happy path via stdin, empty title/summary rejected, missing
      `--summary-file` surfaces a clear error not a traceback, same-day
      same-title collision gets a numbered suffix instead of being
      overwritten)
- [x] Task 7.2: Docs + slash command — update `README.md` and `SPEC.md`
      (done), rewrite the "Saving a session" section of
      `~/.claude/skills/tasker/SKILL.md` to call `session save` directly
      instead of the old two-step process, add
      `~/.claude/commands/save-session.md` (personal slash command) that
      writes a summary to a temp file and runs `tasker session save`

### Checkpoint: Feature 7 complete
- [x] `pytest` passes end-to-end
- [x] Manual check: `tasker session save "test" --summary-file <file>`
      writes `sessions/<date>-test.md` and adds a `Resume session: ...` task
      (verified in an isolated scratch dir)
- [x] Manual check: `/save-session` registered and discoverable as a
      personal slash command (full live-session trigger left for next use)
- [x] README.md / SPEC.md reflect the new command

### Feature 8: Fix id reuse by persisting the id counter (refines Use Case 1)
Approved as part of the follow-up brainstorm in
`sessions/2026-11-10-tasker-improvements.md`. Changes the on-disk shape from
a flat list to `{"next_id": N, "tasks": [...]}`; old-format files still load
via a one-time `max+1` fallback, and the first `save()` after this ships
silently migrates any legacy file (approved one-way migration — the real
`tasks.json` was backed up first).
- [x] Task 8.0: Back up the real `tasks.json` → `tasks.json.bak`
- [x] Task 8.1: `TaskStore.load`/`save` persist `next_id`; legacy flat-list
      files still load via a one-time `max+1` fallback; malformed shapes
      (not list, not `{next_id,tasks}` dict, missing either key, non-int or
      bool `next_id`, `tasks` not a list) raise `TaskStoreError`
- [x] Task 8.2: Update `README.md`/`SPEC.md`

### Checkpoint: Feature 8 complete
- [x] `pytest tests/test_storage.py` passes
- [x] Manual: delete highest id, re-add (fresh process) → new id not reused
- [x] Manual: real `tasks.json` migrated cleanly, both tasks intact
- [x] README/SPEC updated

### Feature 9: Task priority (new Use Case 8)
Also from the same brainstorm. Additive `priority: str = "normal"` field on
`Task` (no migration needed — missing key just falls through to the
dataclass default). Dedicated `priority <id> <level>` command rather than
extending `edit`. Invalid `--priority`/`<level>` values are rejected by
argparse `choices=` (`SystemExit`), not `CliError` — `CliError` stays
reserved for valid-syntax-but-unknown-reference cases like an unknown id.
- [x] Task 9.1: Add `priority: str = "normal"` to `Task` + `PRIORITY_LEVELS`/
      `VALID_PRIORITIES` constants in `models.py`
- [x] Task 9.2: `TaskStore.add()` accepts/validates `priority` (`ValueError`
      on invalid); `load`/`_parse_tasks` rejects an invalid loaded priority
      (`TaskStoreError`); `save()` persists `priority` per task
- [x] Task 9.3: CLI — `add --priority {low,normal,high}` (default `normal`);
      new top-level `priority <id> <low|normal|high>` command; `list_tasks`
      sorts high→normal→low (stable) and appends a `(high)`/`(low)` suffix
      to non-normal tasks
- [x] Task 9.4: Update `SPEC.md` (new Use Case 8) and `README.md`

### Checkpoint: Feature 9 complete
- [x] `pytest` passes end-to-end
- [x] Manual: add high/low/normal tasks, confirm `list` order and suffixes
- [x] Manual: `priority <id> <level>` changes an existing task
- [x] Manual: invalid priority in a hand-edited `tasks.json` → clear error
- [x] README/SPEC updated

### Feature 10: Zero-parameter session save + session list (extends Use Case 6)
Requested after Feature 7 shipped: let `tasker session save` succeed with no
arguments at all (auto-generate title/summary instead of erroring on blank
input), and add `tasker session list` to show what's under `sessions/`.
Full design in `~/.claude/plans/zippy-prancing-chipmunk.md`.
- [x] Task 10.1: Auto-fill title/summary on `session save` (optional title
      positional; `datetime.now()`-based auto title/placeholder summary when
      blank/omitted; avoid blocking on `sys.stdin.read()` when stdin is a
      tty with nothing piped)
- [x] Task 10.2: `session list` command (lists `sessions/*.md`, newest
      first; "No saved sessions." when empty)

### Checkpoint: Feature 10 complete
- [x] `pytest` passes end-to-end
- [x] Manual: `session save` with no args doesn't hang, creates auto-titled
      task + placeholder session file
- [x] Manual: `session save` twice then `session list` → both shown, newest
      first
- [x] README/SPEC updated; `~/.claude/skills/tasker/SKILL.md` commands table
      updated

### Checkpoint: Complete
- [x] All seven original Use Cases implemented and tested
- [x] Feature 8, 9, and 10 (id-reuse fix, priority, auto session save +
      session list) complete
- [x] `pytest` passes end-to-end
- [x] README.md documents install + usage
- [x] `git log` shows one commit per Feature
- [x] Ready for code review

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| argparse subcommand wiring gets fiddly | Low | Keep dispatch functions pure; argparse only parses and calls them |
| Corrupt-JSON edge case under-tested | Low | Explicit test with a hand-written invalid-JSON temp file |

## Open Questions
None.
