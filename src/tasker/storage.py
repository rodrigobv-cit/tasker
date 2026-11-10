import json
from pathlib import Path

from tasker.models import Task


class TaskStoreError(Exception):
    pass


class TaskStore:
    def __init__(self, path: Path, tasks: list[Task]):
        self.path = path
        self._tasks = tasks
        self._next_id = max((t.id for t in tasks), default=0) + 1

    @classmethod
    def load(cls, path: Path) -> "TaskStore":
        if not path.exists():
            return cls(path, [])

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TaskStoreError(f"{path} is not valid JSON: {exc}") from exc

        if not isinstance(raw, list):
            raise TaskStoreError(f"{path} must contain a JSON list of tasks")

        try:
            tasks = [Task(**item) for item in raw]
        except (TypeError, AttributeError) as exc:
            raise TaskStoreError(f"{path} contains a malformed task entry: {exc}") from exc

        return cls(path, tasks)

    def save(self) -> None:
        payload = [
            {"id": t.id, "title": t.title, "done": t.done} for t in self._tasks
        ]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def all(self) -> list[Task]:
        return list(self._tasks)

    def get(self, task_id: int) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def add(self, title: str) -> Task:
        task = Task(id=self._next_id, title=title)
        self._next_id += 1
        self._tasks.append(task)
        return task

    def delete(self, task_id: int) -> bool:
        task = self.get(task_id)
        if task is None:
            return False
        self._tasks.remove(task)
        return True
