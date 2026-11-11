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
- [ ] Task 7.2: Docs + slash command — update `README.md` and `SPEC.md`
      (done), rewrite the "Saving a session" section of
      `~/.claude/skills/tasker/SKILL.md` to call `session save` directly
      instead of the old two-step process, add
      `~/.claude/commands/save-session.md` (personal slash command) that
      writes a summary to a temp file and runs `tasker session save`

### Checkpoint: Feature 7 complete
- [ ] `pytest` passes end-to-end
- [ ] Manual check: `tasker session save "test" --summary-file <file>`
      writes `sessions/<date>-test.md` and adds a `Resume session: ...` task
- [ ] Manual check: `/save-session` works end-to-end in a live session
- [ ] README.md / SPEC.md reflect the new command

### Checkpoint: Complete
- [ ] All seven Use Cases implemented and tested
- [ ] `pytest` passes end-to-end
- [ ] README.md documents install + usage
- [ ] `git log` shows one commit per Feature
- [ ] Ready for code review

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| argparse subcommand wiring gets fiddly | Low | Keep dispatch functions pure; argparse only parses and calls them |
| Corrupt-JSON edge case under-tested | Low | Explicit test with a hand-written invalid-JSON temp file |

## Open Questions
None.
