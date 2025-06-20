import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).with_suffix(".db")


def init_db(path: Path = DB_PATH) -> None:
    """Create the database tables if they do not exist."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inputs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            text TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            input_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            priority TEXT,
            due_date TEXT,
            notes TEXT,
            FOREIGN KEY(input_id) REFERENCES inputs(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            input_id TEXT NOT NULL,
            task_id TEXT,
            content TEXT,
            summary TEXT,
            FOREIGN KEY(input_id) REFERENCES inputs(id),
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        )
        """
    )
    conn.commit()
    conn.close()


def execute(path: Path, query: str, params: Iterable) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def insert_input(input_id: str, timestamp: str, text: str, path: Path = DB_PATH) -> None:
    execute(path, "INSERT INTO inputs(id, timestamp, text) VALUES(?, ?, ?)", (input_id, timestamp, text))


def insert_task(
    task_id: str,
    input_id: str,
    title: str,
    description: str,
    priority: str | None,
    due_date: str | None,
    notes: str | None,
    path: Path = DB_PATH,
) -> None:
    execute(
        path,
        "INSERT INTO tasks(id, input_id, title, description, priority, due_date, notes) VALUES(?, ?, ?, ?, ?, ?, ?)",
        (task_id, input_id, title, description, priority, due_date, notes),
    )


def insert_note(
    note_id: str,
    input_id: str,
    task_id: str | None,
    content: str,
    summary: str,
    path: Path = DB_PATH,
) -> None:
    execute(
        path,
        "INSERT INTO notes(id, input_id, task_id, content, summary) VALUES(?, ?, ?, ?, ?)",
        (note_id, input_id, task_id, content, summary),
    )


def search(path: Path, query: str) -> list[str]:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    pattern = f"%{query}%"
    cur.execute(
        "SELECT title FROM tasks WHERE title LIKE ? OR description LIKE ? ORDER BY rowid DESC LIMIT 10",
        (pattern, pattern),
    )
    task_results = [row[0] for row in cur.fetchall()]
    cur.execute(
        "SELECT content FROM notes WHERE content LIKE ? ORDER BY rowid DESC LIMIT 10",
        (pattern,),
    )
    note_results = [row[0] for row in cur.fetchall()]
    conn.close()
    return task_results + note_results
