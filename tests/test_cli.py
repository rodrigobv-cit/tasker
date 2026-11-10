import pytest

from tasker.cli import CliError, run
from tasker.storage import TaskStore


def test_add_creates_task_and_prints_confirmation(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    output = run(store, ["add", "Buy milk"])
    assert output == "Added #1: Buy milk"
    assert [t.title for t in store.all()] == ["Buy milk"]


def test_add_rejects_empty_title(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    with pytest.raises(CliError):
        run(store, ["add", "  "])
    assert store.all() == []
