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


def test_list_empty_store_prints_friendly_message(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    assert run(store, ["list"]) == "No tasks."


def test_list_all_shows_every_task_with_status(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    done = store.add("Walk the dog")
    done.done = True

    output = run(store, ["list"])
    assert output == "[ ] #1 Buy milk\n[x] #2 Walk the dog"


def test_list_pending_filters_to_unfinished(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    done = store.add("Walk the dog")
    done.done = True

    assert run(store, ["list", "--pending"]) == "[ ] #1 Buy milk"


def test_list_done_filters_to_finished(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    done = store.add("Walk the dog")
    done.done = True

    assert run(store, ["list", "--done"]) == "[x] #2 Walk the dog"


def test_done_marks_task_complete(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")

    output = run(store, ["done", "1"])
    assert output == "Task #1 marked done."
    assert store.get(1).done is True


def test_done_unknown_id_raises_without_changing_file(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    with pytest.raises(CliError):
        run(store, ["done", "999"])


def test_done_already_done_is_idempotent(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    run(store, ["done", "1"])

    output = run(store, ["done", "1"])
    assert output == "Task #1 is already done."


def test_edit_updates_title_only(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    run(store, ["done", "1"])

    output = run(store, ["edit", "1", "Buy oat milk"])
    assert output == "Task #1 updated: Buy oat milk"
    task = store.get(1)
    assert task.title == "Buy oat milk"
    assert task.done is True


def test_edit_unknown_id_raises(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    with pytest.raises(CliError):
        run(store, ["edit", "999", "new title"])


def test_delete_removes_task(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")

    output = run(store, ["delete", "1"])
    assert output == "Task #1 deleted."
    assert store.get(1) is None


def test_delete_unknown_id_raises_without_changing_file(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    with pytest.raises(CliError):
        run(store, ["delete", "999"])
    assert len(store.all()) == 1
