import argparse
import sys
from pathlib import Path

from tasker.storage import TaskStore, TaskStoreError


class CliError(Exception):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasker")
    parser.add_argument("--file", default="tasks.json", help="path to the tasks JSON file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="add a new task")
    add_parser.add_argument("title")

    list_parser = subparsers.add_parser("list", help="list tasks")
    filter_group = list_parser.add_mutually_exclusive_group()
    filter_group.add_argument("--pending", action="store_true")
    filter_group.add_argument("--done", action="store_true")

    return parser


def add_task(store: TaskStore, title: str) -> str:
    title = title.strip()
    if not title:
        raise CliError("title must not be empty")
    task = store.add(title)
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

    lines = [f"[{'x' if t.done else ' '}] #{t.id} {t.title}" for t in tasks]
    return "\n".join(lines)


def run(store: TaskStore, argv: list[str]) -> str:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "add":
        return add_task(store, args.title)
    if args.command == "list":
        return list_tasks(store, pending=args.pending, done=args.done)

    raise CliError(f"unknown command: {args.command}")


def main() -> int:
    argv = sys.argv[1:]
    try:
        file_path = Path(_extract_file_option(argv))
        store = TaskStore.load(file_path)
        print(run(store, argv))
    except TaskStoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def _extract_file_option(argv: list[str]) -> str:
    return build_parser().parse_args(argv).file


if __name__ == "__main__":
    sys.exit(main())
