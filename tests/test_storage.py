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


@pytest.mark.parametrize(
    "content",
    [
        "{}",
        "null",
        '[{"id": 1}]',
        '[{"id": 1, "title": "x", "done": false, "priority": "high"}]',
        '{"tasks": []}',
        '{"next_id": 1}',
        '{"next_id": "x", "tasks": []}',
        '{"next_id": true, "tasks": []}',
        '{"next_id": 1, "tasks": "nope"}',
    ],
)
def test_load_malformed_shape_raises_clear_error_not_traceback(tmp_path, content):
    path = tmp_path / "tasks.json"
    path.write_text(content, encoding="utf-8")
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
    assert raw == {"next_id": 2, "tasks": [{"id": 1, "title": "Buy milk", "done": False}]}


def test_load_old_list_format_still_loads(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text(
        json.dumps([{"id": 1, "title": "Legacy one", "done": False},
                    {"id": 2, "title": "Legacy two", "done": True}]),
        encoding="utf-8",
    )
    store = TaskStore.load(path)
    assert [t.title for t in store.all()] == ["Legacy one", "Legacy two"]


def test_load_old_list_format_computes_next_id_from_max_with_gaps(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text(
        json.dumps([{"id": 1, "title": "a", "done": False},
                    {"id": 5, "title": "b", "done": False}]),
        encoding="utf-8",
    )
    store = TaskStore.load(path)
    new_task = store.add("c")
    assert new_task.id == 6


def test_save_after_loading_old_format_migrates_to_object_shape(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text(
        json.dumps([{"id": 1, "title": "Legacy one", "done": False}]),
        encoding="utf-8",
    )
    store = TaskStore.load(path)
    store.save()

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw == {"next_id": 2, "tasks": [{"id": 1, "title": "Legacy one", "done": False}]}

    reloaded = TaskStore.load(path)
    assert [t.title for t in reloaded.all()] == ["Legacy one"]


def test_delete_highest_id_then_add_does_not_reuse_id(tmp_path):
    path = tmp_path / "tasks.json"
    store = TaskStore.load(path)
    store.add("a")
    store.add("b")
    store.add("c")
    store.delete(3)
    store.save()

    reloaded = TaskStore.load(path)
    new_task = reloaded.add("d")
    assert new_task.id == 4


def test_get_returns_task_by_id(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    task = store.add("Buy milk")
    assert store.get(task.id) is task


def test_get_unknown_id_returns_none(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    assert store.get(999) is None
