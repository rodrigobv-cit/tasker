import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

from tasker.models import PRIORITY_LEVELS
from tasker.storage import TaskStore, TaskStoreError


class CliError(Exception):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasker")
    parser.add_argument("--file", default="tasks.json", help="path to the tasks JSON file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="add a new task")
    add_parser.add_argument("title")
    add_parser.add_argument("--priority", choices=["low", "normal", "high"], default="normal")

    list_parser = subparsers.add_parser("list", help="list tasks")
    filter_group = list_parser.add_mutually_exclusive_group()
    filter_group.add_argument("--all", action="store_true", help="show every task (default)")
    filter_group.add_argument("--pending", action="store_true")
    filter_group.add_argument("--done", action="store_true")

    done_parser = subparsers.add_parser("done", help="mark a task done")
    done_parser.add_argument("id", type=int)

    edit_parser = subparsers.add_parser("edit", help="edit a task's title")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("title")

    delete_parser = subparsers.add_parser("delete", help="delete a task")
    delete_parser.add_argument("id", type=int)

    priority_parser = subparsers.add_parser("priority", help="change a task's priority")
    priority_parser.add_argument("id", type=int)
    priority_parser.add_argument("level", choices=["low", "normal", "high"])

    session_parser = subparsers.add_parser("session", help="manage resumable session tasks")
    session_subparsers = session_parser.add_subparsers(dest="session_command", required=True)
    session_save_parser = session_subparsers.add_parser(
        "save", help="write a session summary and link a resumable task to it"
    )
    session_save_parser.add_argument("title", nargs="?", default=None)
    session_save_parser.add_argument(
        "--summary-file",
        dest="summary_file",
        default=None,
        help="path to the summary content; omit to read it from stdin",
    )

    session_subparsers.add_parser("list", help="list saved session files")

    return parser


def add_task(store: TaskStore, title: str, priority: str = "normal") -> str:
    title = title.strip()
    if not title:
        raise CliError("title must not be empty")
    task = store.add(title, priority=priority)
    store.save()
    return f"Added #{task.id}: {task.title}"


def list_tasks(store: TaskStore, *, pending: bool = False, done: bool = False) -> str:
    tasks = store.all()
    if pending:
        tasks = [t for t in tasks if not t.done]
    elif done:
        tasks = [t for t in tasks if t.done]

    if not tasks:
        return "No tasks."

    order = {level: i for i, level in enumerate(PRIORITY_LEVELS)}
    tasks = sorted(tasks, key=lambda t: order[t.priority])  # stable: keeps insertion order within a tier

    lines = []
    for t in tasks:
        suffix = f" ({t.priority})" if t.priority != "normal" else ""
        lines.append(f"[{'x' if t.done else ' '}] #{t.id} {t.title}{suffix}")
    return "\n".join(lines)


def set_priority(store: TaskStore, task_id: int, level: str) -> str:
    task = store.get(task_id)
    if task is None:
        raise CliError(f"no task with id {task_id}")
    task.priority = level
    store.save()
    return f"Task #{task_id} priority set to {level}."


def complete_task(store: TaskStore, task_id: int) -> str:
    task = store.get(task_id)
    if task is None:
        raise CliError(f"no task with id {task_id}")
    if task.done:
        return f"Task #{task_id} is already done."
    task.done = True
    store.save()
    return f"Task #{task_id} marked done."


def edit_task(store: TaskStore, task_id: int, title: str) -> str:
    task = store.get(task_id)
    if task is None:
        raise CliError(f"no task with id {task_id}")
    title = title.strip()
    if not title:
        raise CliError("title must not be empty")
    task.title = title
    store.save()
    return f"Task #{task_id} updated: {title}"


def delete_task(store: TaskStore, task_id: int) -> str:
    if not store.delete(task_id):
        raise CliError(f"no task with id {task_id}")
    store.save()
    return f"Task #{task_id} deleted."


def save_session(store: TaskStore, title: str | None, summary: str) -> str:
    title = (title or "").strip()
    if not title:
        title = f"Session {datetime.now():%Y-%m-%d %H:%M:%S}"
    summary = summary.strip()
    if not summary:
        summary = f"Auto-saved session (no summary provided) at {datetime.now():%Y-%m-%d %H:%M:%S}."

    sessions_dir = store.path.parent / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    filename = _session_filename(sessions_dir, title)
    (sessions_dir / filename).write_text(summary + "\n", encoding="utf-8")

    task = store.add(f"Resume session: {title} (see sessions/{filename})")
    store.save()
    return f"Saved session to sessions/{filename}\nAdded #{task.id}: {task.title}"


def _session_filename(sessions_dir: Path, title: str) -> str:
    slug = _slugify(title)
    base = f"{date.today().isoformat()}-{slug}"
    filename = f"{base}.md"
    counter = 2
    while (sessions_dir / filename).exists():
        filename = f"{base}-{counter}.md"
        counter += 1
    return filename


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:40].strip("-") or "session"


def list_sessions(store: TaskStore) -> str:
    sessions_dir = store.path.parent / "sessions"
    if not sessions_dir.exists():
        return "No saved sessions."
    files = sorted(sessions_dir.glob("*.md"), reverse=True)
    if not files:
        return "No saved sessions."
    return "\n".join(f"sessions/{f.name}" for f in files)


def run(store: TaskStore, argv: list[str]) -> str:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "add":
        return add_task(store, args.title, priority=args.priority)
    if args.command == "list":
        return list_tasks(store, pending=args.pending, done=args.done)
    if args.command == "done":
        return complete_task(store, args.id)
    if args.command == "edit":
        return edit_task(store, args.id, args.title)
    if args.command == "delete":
        return delete_task(store, args.id)
    if args.command == "priority":
        return set_priority(store, args.id, args.level)
    if args.command == "session" and args.session_command == "save":
        if args.summary_file:
            try:
                summary = Path(args.summary_file).read_text(encoding="utf-8")
            except OSError as exc:
                raise CliError(f"could not read summary file: {exc}") from exc
        elif not sys.stdin.isatty():
            summary = sys.stdin.read()
        else:
            summary = ""
        return save_session(store, args.title, summary)
    if args.command == "session" and args.session_command == "list":
        return list_sessions(store)

    raise CliError(f"unknown command: {args.command}")


def main() -> int:
    argv = sys.argv[1:]
    try:
        file_path = Path(_extract_file_option(argv))
        store = TaskStore.load(file_path)
        print(run(store, argv))
    except (TaskStoreError, CliError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def _extract_file_option(argv: list[str]) -> str:
    return build_parser().parse_args(argv).file


if __name__ == "__main__":
    sys.exit(main())
