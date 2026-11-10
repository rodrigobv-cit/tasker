---
name: tasker
description: Add, list, complete, edit, or delete personal to-do tasks using the local "tasker" CLI tool built in this project. Use this skill whenever the user asks to add a task, create a to-do, mark something done/complete, check their task list, see what's pending, edit or rename a task, or delete/remove a task — even if they don't say "tasker" by name, e.g. "add finish the report to my list", "what do I still need to do", "mark #2 done", "remove the milk task". Always use this skill instead of reading or writing tasks.json directly.
---

# tasker CLI skill

Wraps the `tasker` CLI (built in this repo: `SPEC.md`, `src/tasker/`) so task
management requests are handled by running the real tool instead of editing
`tasks.json` by hand or re-deriving command syntax from scratch.

## Why run the CLI instead of editing tasks.json directly

`tasker` is the single source of truth for id assignment, validation (no
empty titles, no unknown ids) and the on-disk JSON shape. Editing the file
directly risks duplicate/invalid ids and skips those checks — always go
through the CLI.

## How to invoke it

Always call the CLI with its full path and an explicit `--file` pointing at
this project's `tasks.json`, so it works correctly no matter what directory
the command happens to run from:

```bash
# Bash / Git Bash
"C:/Users/rodrigobv/code/task-tracker/.venv/Scripts/tasker" --file "C:/Users/rodrigobv/code/task-tracker/tasks.json" <command> [args]
```

```powershell
# PowerShell
& "C:\Users\rodrigobv\code\task-tracker\.venv\Scripts\tasker.exe" --file "C:\Users\rodrigobv\code\task-tracker\tasks.json" <command> [args]
```

`--file` must come *before* the subcommand — it's a top-level option, not a
per-command one.

## Commands

| User says | Run |
|---|---|
| Add a task | `... add "<title>"` |
| List everything | `... list` |
| List what's left to do | `... list --pending` |
| List what's finished | `... list --done` |
| Mark a task done/complete | `... done <id>` |
| Rename / edit a task's title | `... edit <id> "<new title>"` |
| Delete / remove a task | `... delete <id>` |

Task ids come from a prior `list` — if the user names a task by title rather
than id ("mark the milk task done"), run `list` first to resolve the id,
then confirm which one you mean if more than one title matches.

## Output and errors

The CLI prints a one-line confirmation on success (e.g. `Added #3: Buy milk`,
`Task #3 deleted.`) — relay that line back to the user rather than
paraphrasing it. On failure it exits non-zero and prints `Error: <reason>` to
stderr (unknown id, empty title, corrupt/malformed `tasks.json`) — surface
that message directly; don't guess at a fix or silently retry.

## Example

```bash
"C:/Users/rodrigobv/code/task-tracker/.venv/Scripts/tasker" --file "C:/Users/rodrigobv/code/task-tracker/tasks.json" add "Finish studying CCAR-P"
# -> Added #1: Finish studying CCAR-P
```
