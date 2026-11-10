---
name: tasker
description: Add, list, complete, edit, or delete personal to-do tasks using the local "tasker" CLI tool built in this project. Use this skill whenever the user asks to add a task, create a to-do, mark something done/complete, check their task list or "pending tasks", see what's pending, edit or rename a task, delete/remove a task, save their current session/progress, or resume a previous session — even if they don't say "tasker" by name, e.g. "add finish the report to my list", "what do I still need to do", "mark #2 done", "remove the milk task", "pending tasks", "save this session", "resume where I left off". Always use this skill instead of reading or writing tasks.json directly.
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

## "pending tasks": also surface tasks from the conversation, with approval

When the user's message is essentially just **"pending tasks"** (or a close
variant — "show pending tasks", "what are my pending tasks"), do two things,
not just one:

1. Run `... list --pending` and show the real result.
2. Separately, re-read the current conversation for projects, follow-ups, or
   action items that came up but aren't in that list yet — a decision that
   needs a follow-up, a "I still need to..." aside, something the user said
   they'd get back to. Propose these as **candidate** new tasks.

For step 2, never call `add` directly. List each candidate with its proposed
title and ask the user to approve it, one by one or as a batch — e.g.:

```
From this conversation, I'd also add:
1. "Review the Q3 budget doc Sarah sent"
2. "Follow up with the vendor about the delayed shipment"
Add these? (yes / no / edit one)
```

Only call `tasker add` for the ones the user explicitly approves. Skip step
2 entirely if nothing in the conversation looks like an actual task — don't
invent busywork to fill the list.

## Saving a session so it can be resumed later

`tasker` tasks are just a title, so a task alone can't hold enough context to
pick a complex piece of work back up. When the user is about to stop (they
say they're done for now, switching contexts, or asks to "save this session"
or "save my progress"), suggest capturing it as a resumable task:

1. Write a short markdown summary of the session — what was being worked on,
   key decisions made, and concrete next steps — to
   `sessions/<YYYY-MM-DD>-<short-slug>.md` in this project (create the
   `sessions/` directory if it doesn't exist; it's gitignored, same as
   `tasks.json` — these are working notes, not project history).
2. Add a task whose title follows this exact convention so it's recognized
   later: `Resume session: <short description> (see sessions/<file>.md)`.

Example:
```
... add "Resume session: SPEC review for the billing feature (see sessions/2026-11-10-billing-spec.md)"
```

Don't do this automatically — offer it ("Want me to save a session you can
resume later?") and only write the file/task once the user agrees.

## Resuming a saved session

If the user asks to resume a session, or picks one that was surfaced at
session start (see below): find the matching task (`list --pending` if you
don't already have the id), read the markdown file its title points to for
context, and pick the work back up from there. Once the resumed work is
actually finished, mark that task `done` (or `delete` it) — don't leave a
stale "Resume session: ..." task hanging around once it no longer applies.

## Session start: pending tasks shown automatically

A `SessionStart` hook (`.claude/settings.json` →
`.claude/hooks/session_start.py`) already runs `tasker list --pending` the
moment a new Claude Code session starts in this project, and injects the
result as context for you — the user hasn't typed anything yet. When you
see that context at the start of a session:

1. Show the pending task list to the user without waiting to be asked.
2. If any task's title contains `Resume session:`, point it out specifically
   and ask whether they want to resume it before anything else.

If the hook's context is missing or empty (e.g. it's the very first run with
no tasks yet), there's nothing to show — don't fabricate a task list.

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
