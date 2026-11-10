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
