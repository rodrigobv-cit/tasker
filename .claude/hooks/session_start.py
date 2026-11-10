"""SessionStart hook: surfaces tasker's pending tasks as context for the new session.

Runs the tasker CLI (absolute paths, so it works regardless of the hook's
cwd) and emits a SessionStart hookSpecificOutput so Claude sees the pending
list immediately, without the user having to ask. See
.claude/skills/tasker/SKILL.md for what the model should do with it.
"""

import json
import subprocess

TASKER = r"C:\Users\rodrigobv\code\task-tracker\.venv\Scripts\tasker"
TASKS_FILE = r"C:\Users\rodrigobv\code\task-tracker\tasks.json"
RESUME_PREFIX = "Resume session:"


def main() -> None:
    try:
        result = subprocess.run(
            [TASKER, "--file", TASKS_FILE, "list", "--pending"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        listing = (result.stdout or result.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as exc:
        listing = f"(tasker could not be run: {exc})"

    resumable = [
        line for line in listing.splitlines() if RESUME_PREFIX in line
    ]

    context_lines = [
        "tasker pending tasks for this project (from `tasker list --pending`):",
        listing,
    ]
    if resumable:
        context_lines.append(
            "\nOne or more pending tasks look like a saved session "
            f"(title contains \"{RESUME_PREFIX}\"). Before anything else, "
            "ask the user whether they want to resume one of these — show "
            "the task's id and title, and if they say yes, read whatever "
            "file the title references for context before continuing that "
            "work."
        )
    context_lines.append(
        "\nShow the pending task list to the user at the start of this "
        "session. Don't silently skip this."
    )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(context_lines),
        }
    }))


if __name__ == "__main__":
    main()
