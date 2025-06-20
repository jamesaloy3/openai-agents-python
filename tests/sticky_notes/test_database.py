from pathlib import Path

from examples.sticky_notes.database import init_db, insert_input, search, DB_PATH


def test_db_insert_and_search(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    init_db(db)
    insert_input("id1", "now", "test task", db)
    results = search(db, "test")
    assert results
