from pathlib import Path

from examples.sticky_notes.database import (
    init_db,
    insert_input,
    insert_task,
    insert_note,
    search,
    DB_PATH,
)


def test_db_insert_and_search(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    init_db(db)
    insert_input("id1", "now", "test task", db)
    results = search(db, "test")
    assert results


def test_insert_task_and_note(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    init_db(db)
    insert_task("t1", "in1", "demo", "demo description", None, None, None, db)
    insert_note("n1", "in1", "t1", "content", "summary", db)
    results = search(db, "demo")
    assert "demo" in results[0]
