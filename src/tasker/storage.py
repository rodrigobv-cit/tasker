import json
from pathlib import Path

from tasker.models import Task, VALID_PRIORITIES


class TaskStoreError(Exception):
    pass


class TaskStore:
    def __init__(self, path: Path, tasks: list[Task], next_id: int | None = None):
        self.path = path
        self._tasks = tasks
        self._next_id = next_id if next_id is not None else max((t.id for t in tasks), default=0) + 1

    @classmethod
    def load(cls, path: Path) -> "TaskStore":
        if not path.exists():
            return cls(path, [], next_id=1)

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TaskStoreError(f"{path} is not valid JSON: {exc}") from exc

        if isinstance(raw, list):
            tasks = cls._parse_tasks(raw, path)
            return cls(path, tasks)

        if isinstance(raw, dict) and "next_id" in raw and "tasks" in raw:
            next_id = raw["next_id"]
            if not isinstance(next_id, int) or isinstance(next_id, bool):
                raise TaskStoreError(f"{path} has a non-integer next_id")
            if not isinstance(raw["tasks"], list):
                raise TaskStoreError(f"{path} 'tasks' must be a JSON list")
            tasks = cls._parse_tasks(raw["tasks"], path)
            return cls(path, tasks, next_id=next_id)

        raise TaskStoreError(f"{path} must be a JSON list or an object with 'next_id' and 'tasks'")

    @staticmethod
    def _parse_tasks(raw_tasks: list, path: Path) -> list[Task]:
        try:
            tasks = [Task(**item) for item in raw_tasks]
        except (TypeError, AttributeError) as exc:
            raise TaskStoreError(f"{path} contains a malformed task entry: {exc}") from exc
        for task in tasks:
            if task.priority not in VALID_PRIORITIES:
                raise TaskStoreError(f"{path} contains a task with an invalid priority: {task.priority!r}")
        return tasks

    def save(self) -> None:
        payload = {
            "next_id": self._next_id,
            "tasks": [
                {"id": t.id, "title": t.title, "done": t.done, "priority": t.priority}
                for t in self._tasks
            ],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def all(self) -> list[Task]:
        return list(self._tasks)

    def get(self, task_id: int) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def add(self, title: str, priority: str = "normal") -> Task:
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"invalid priority: {priority!r}")
        task = Task(id=self._next_id, title=title, priority=priority)
        self._next_id += 1
        self._tasks.append(task)
        return task

    def delete(self, task_id: int) -> bool:
        task = self.get(task_id)
        if task is None:
            return False
        self._tasks.remove(task)
        return True
