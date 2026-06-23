# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import List

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI(title="Task API")

DB_PATH = "tasks.db"


def get_db():
    """Dependency that provides a SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create the tasks table if it does not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT
        )
        """
    )
    conn.commit()
    conn.close()


class TaskCreate(BaseModel):
    title: str
    description: str = None


class Task(BaseModel):
    id: int
    title: str
    description: str = None


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description) VALUES (?, ?)",
        (task.title, task.description),
    )
    db.commit()
    task_id = cursor.lastrowid
    cursor.execute("SELECT id, title, description FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    return Task(id=row["id"], title=row["title"], description=row["description"])


@app.get("/tasks", response_model=List[Task])
def list_tasks(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, title, description FROM tasks")
    rows = cursor.fetchall()
    return [Task(id=row["id"], title=row["title"], description=row["description"]) for row in rows]


if __name__ == "__main__":
    import os, uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))))