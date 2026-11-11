from dataclasses import dataclass

PRIORITY_LEVELS = ("high", "normal", "low")
VALID_PRIORITIES = frozenset(PRIORITY_LEVELS)


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    priority: str = "normal"
