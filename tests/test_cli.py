from datetime import date

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


def test_list_explicit_all_flag_matches_default(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    done = store.add("Walk the dog")
    done.done = True

    assert run(store, ["list", "--all"]) == run(store, ["list"])


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


def test_edit_rejects_empty_title(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    with pytest.raises(CliError):
        run(store, ["edit", "1", "   "])
    assert store.get(1).title == "Buy milk"


def test_add_with_priority_flag_sets_priority(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    run(store, ["add", "Buy milk", "--priority", "high"])
    assert store.get(1).priority == "high"


def test_add_rejects_invalid_priority_flag(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    with pytest.raises(SystemExit):
        run(store, ["add", "Buy milk", "--priority", "urgent"])
    assert store.all() == []


def test_priority_command_updates_existing_task(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")

    output = run(store, ["priority", "1", "low"])
    assert output == "Task #1 priority set to low."
    assert store.get(1).priority == "low"


def test_priority_command_unknown_id_raises(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    with pytest.raises(CliError):
        run(store, ["priority", "999", "low"])


def test_priority_command_rejects_invalid_level(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk")
    with pytest.raises(SystemExit):
        run(store, ["priority", "1", "urgent"])
    assert store.get(1).priority == "normal"


def test_list_sorts_by_priority_preserving_insertion_order_within_tier(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("normal one")
    store.add("high one", priority="high")
    store.add("low one", priority="low")
    store.add("normal two")
    store.add("high two", priority="high")

    output = run(store, ["list"])
    assert output == (
        "[ ] #2 high one (high)\n"
        "[ ] #5 high two (high)\n"
        "[ ] #1 normal one\n"
        "[ ] #4 normal two\n"
        "[ ] #3 low one (low)"
    )


def test_list_output_marks_non_normal_priority(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("Buy milk", priority="high")

    assert run(store, ["list"]) == "[ ] #1 Buy milk (high)"


def test_list_pending_and_done_filters_still_sort_by_priority(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    store.add("normal pending")
    high_done = store.add("high done", priority="high")
    high_done.done = True
    low_pending = store.add("low pending", priority="low")

    assert run(store, ["list", "--pending"]) == (
        "[ ] #1 normal pending\n[ ] #3 low pending (low)"
    )
    assert run(store, ["list", "--done"]) == "[x] #2 high done (high)"


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


def test_session_save_writes_file_and_creates_linked_task(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    summary_file = tmp_path / "notes.md"
    summary_file.write_text("Status: in progress.", encoding="utf-8")

    output = run(store, ["session", "save", "My Session", "--summary-file", str(summary_file)])

    today = date.today().isoformat()
    expected_filename = f"{today}-my-session.md"
    assert output == (
        f"Saved session to sessions/{expected_filename}\n"
        f"Added #1: Resume session: My Session (see sessions/{expected_filename})"
    )
    saved = tmp_path / "sessions" / expected_filename
    assert saved.read_text(encoding="utf-8") == "Status: in progress.\n"
    assert store.all()[0].title == f"Resume session: My Session (see sessions/{expected_filename})"


def test_session_save_reads_summary_from_stdin_when_no_file_given(tmp_path, monkeypatch):
    import io

    store = TaskStore.load(tmp_path / "tasks.json")
    monkeypatch.setattr("sys.stdin", io.StringIO("Piped summary."))

    run(store, ["session", "save", "Piped"])

    today = date.today().isoformat()
    saved = tmp_path / "sessions" / f"{today}-piped.md"
    assert saved.read_text(encoding="utf-8") == "Piped summary.\n"


def test_session_save_blank_title_falls_back_to_auto_title(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    summary_file = tmp_path / "notes.md"
    summary_file.write_text("content", encoding="utf-8")

    run(store, ["session", "save", "  ", "--summary-file", str(summary_file)])

    assert store.all()[0].title.startswith("Resume session: Session ")


def test_session_save_blank_summary_falls_back_to_placeholder(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    summary_file = tmp_path / "notes.md"
    summary_file.write_text("   ", encoding="utf-8")

    run(store, ["session", "save", "My Session", "--summary-file", str(summary_file)])

    today = date.today().isoformat()
    saved = tmp_path / "sessions" / f"{today}-my-session.md"
    assert saved.read_text(encoding="utf-8").startswith("Auto-saved session")


class _FakeTty:
    def isatty(self):
        return True

    def read(self):
        raise AssertionError("stdin should not be read when it's a tty with no --summary-file")


def test_session_save_with_no_arguments_auto_fills_everything(tmp_path, monkeypatch):
    store = TaskStore.load(tmp_path / "tasks.json")
    monkeypatch.setattr("sys.stdin", _FakeTty())

    run(store, ["session", "save"])

    task = store.all()[0]
    assert task.title.startswith("Resume session: Session ")
    sessions_dir = tmp_path / "sessions"
    saved_files = list(sessions_dir.glob("*.md"))
    assert len(saved_files) == 1
    assert saved_files[0].read_text(encoding="utf-8").startswith("Auto-saved session")


def test_session_save_with_title_but_no_pipe_uses_placeholder_summary(tmp_path, monkeypatch):
    store = TaskStore.load(tmp_path / "tasks.json")
    monkeypatch.setattr("sys.stdin", _FakeTty())

    run(store, ["session", "save", "Real title"])

    today = date.today().isoformat()
    saved = tmp_path / "sessions" / f"{today}-real-title.md"
    assert saved.read_text(encoding="utf-8").startswith("Auto-saved session")
    assert store.all()[0].title == f"Resume session: Real title (see sessions/{today}-real-title.md)"


def test_session_save_missing_summary_file_raises_clear_error(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    missing = tmp_path / "does-not-exist.md"

    with pytest.raises(CliError):
        run(store, ["session", "save", "My Session", "--summary-file", str(missing)])
    assert store.all() == []


def test_session_save_collision_gets_numbered_suffix_without_overwriting(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    first_file = tmp_path / "first.md"
    first_file.write_text("First summary.", encoding="utf-8")
    second_file = tmp_path / "second.md"
    second_file.write_text("Second summary.", encoding="utf-8")

    run(store, ["session", "save", "My Session", "--summary-file", str(first_file)])
    run(store, ["session", "save", "My Session", "--summary-file", str(second_file)])

    today = date.today().isoformat()
    sessions_dir = tmp_path / "sessions"
    assert (sessions_dir / f"{today}-my-session.md").read_text(encoding="utf-8") == "First summary.\n"
    assert (sessions_dir / f"{today}-my-session-2.md").read_text(encoding="utf-8") == "Second summary.\n"
    assert len(store.all()) == 2


def test_session_list_with_no_sessions_dir_prints_friendly_message(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")

    assert run(store, ["session", "list"]) == "No saved sessions."


def test_session_list_shows_saved_files_newest_first(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    first_file = tmp_path / "first.md"
    first_file.write_text("First.", encoding="utf-8")
    second_file = tmp_path / "second.md"
    second_file.write_text("Second.", encoding="utf-8")

    run(store, ["session", "save", "Alpha", "--summary-file", str(first_file)])
    run(store, ["session", "save", "Zeta", "--summary-file", str(second_file)])

    today = date.today().isoformat()
    assert run(store, ["session", "list"]) == (
        f"sessions/{today}-zeta.md\nsessions/{today}-alpha.md"
    )


def test_session_list_orders_same_title_collisions_by_save_time_not_filename_text(tmp_path):
    store = TaskStore.load(tmp_path / "tasks.json")
    first_file = tmp_path / "first.md"
    first_file.write_text("First.", encoding="utf-8")
    second_file = tmp_path / "second.md"
    second_file.write_text("Second.", encoding="utf-8")

    run(store, ["session", "save", "My Session", "--summary-file", str(first_file)])
    run(store, ["session", "save", "My Session", "--summary-file", str(second_file)])

    today = date.today().isoformat()
    assert run(store, ["session", "list"]) == (
        f"sessions/{today}-my-session-2.md\nsessions/{today}-my-session.md"
    )
