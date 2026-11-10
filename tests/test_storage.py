import json

import pytest

from tasker.storage import TaskStore, TaskStoreError


def test_load_missing_file_returns_empty_store(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    assert store.all() == []


def test_load_corrupt_json_raises_clear_error(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(TaskStoreError):
        TaskStore.load(path)


def test_add_assigns_unique_incrementing_ids(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    first = store.add("Buy milk")
    second = store.add("Walk the dog")
    assert first.id == 1
    assert second.id == 2


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "tasks.json"
    store = TaskStore.load(path)
    store.add("Buy milk")
    store.save()

    reloaded = TaskStore.load(path)
    assert [t.title for t in reloaded.all()] == ["Buy milk"]


def test_save_writes_valid_json(tmp_path):
    path = tmp_path / "tasks.json"
    store = TaskStore.load(path)
    store.add("Buy milk")
    store.save()

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw == [{"id": 1, "title": "Buy milk", "done": False}]


def test_get_returns_task_by_id(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    task = store.add("Buy milk")
    assert store.get(task.id) is task


def test_get_unknown_id_returns_none(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    assert store.get(999) is None
