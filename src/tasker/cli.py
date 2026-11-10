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

    return parser


def add_task(store: TaskStore, title: str) -> str:
    title = title.strip()
    if not title:
        raise CliError("title must not be empty")
    task = store.add(title)
    store.save()
    return f"Added #{task.id}: {task.title}"


def run(store: TaskStore, argv: list[str]) -> str:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "add":
        return add_task(store, args.title)

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
