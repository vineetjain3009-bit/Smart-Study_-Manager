"""SQLite data layer for Smart Study Manager.

Keeping SQL in one small module makes the Tkinter pages easier to read and
also gives the project a clear example of database CRUD operations.
"""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional


class Database:
    """Creates and works with the local SQLite database."""

    def __init__(self, database_path: Optional[Path] = None) -> None:
        project_dir = Path(__file__).resolve().parent
        self.path = database_path or project_dir / "database" / "study_manager.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Provide a committing connection and always release its file handle."""
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def create_tables(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    teacher TEXT,
                    UNIQUE(user_id, code),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    deadline TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    session_date TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    total_classes INTEGER NOT NULL DEFAULT 0,
                    attended_classes INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(user_id, subject_id),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                );
                """
            )

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # --- User operations -------------------------------------------------
    def register_user(self, username: str, password: str, full_name: str) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
                    (username.strip(), self.hash_password(password), full_name.strip(), datetime.now().isoformat(timespec="seconds")),
                )
            return True, "Registration successful. You can now log in."
        except sqlite3.IntegrityError:
            return False, "That username is already in use."
        except sqlite3.Error as error:
            return False, f"Could not create the account: {error}"

    def authenticate(self, username: str, password: str) -> Optional[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT id, username, full_name FROM users WHERE username = ? AND password_hash = ?",
                (username.strip(), self.hash_password(password)),
            ).fetchone()

    # --- Subject operations ---------------------------------------------
    def get_subjects(self, user_id: int) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM subjects WHERE user_id = ? ORDER BY code COLLATE NOCASE", (user_id,)
            ).fetchall()

    def add_subject(self, user_id: int, code: str, name: str, teacher: str) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO subjects (user_id, code, name, teacher) VALUES (?, ?, ?, ?)",
                    (user_id, code.strip().upper(), name.strip(), teacher.strip()),
                )
            return True, "Subject added successfully."
        except sqlite3.IntegrityError:
            return False, "A subject with this code already exists."
        except sqlite3.Error as error:
            return False, f"Could not save subject: {error}"

    def update_subject(self, subject_id: int, user_id: int, code: str, name: str, teacher: str) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                result = conn.execute(
                    "UPDATE subjects SET code = ?, name = ?, teacher = ? WHERE id = ? AND user_id = ?",
                    (code.strip().upper(), name.strip(), teacher.strip(), subject_id, user_id),
                )
            return (True, "Subject updated successfully.") if result.rowcount else (False, "Subject not found.")
        except sqlite3.IntegrityError:
            return False, "A subject with this code already exists."
        except sqlite3.Error as error:
            return False, f"Could not update subject: {error}"

    def delete_subject(self, subject_id: int, user_id: int) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                result = conn.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
            return (True, "Subject deleted.") if result.rowcount else (False, "Subject not found.")
        except sqlite3.Error as error:
            return False, f"Could not delete subject: {error}"

    # --- Task operations -------------------------------------------------
    def get_tasks(self, user_id: int, status: str = "All") -> list[sqlite3.Row]:
        sql = """
            SELECT tasks.*, COALESCE(subjects.code, 'No subject') AS subject_code
            FROM tasks LEFT JOIN subjects ON tasks.subject_id = subjects.id
            WHERE tasks.user_id = ?
        """
        parameters: list[object] = [user_id]
        if status in ("Pending", "Completed"):
            sql += " AND tasks.status = ?"
            parameters.append(status)
        sql += " ORDER BY CASE tasks.status WHEN 'Pending' THEN 0 ELSE 1 END, tasks.deadline"
        with self.connect() as conn:
            return conn.execute(sql, parameters).fetchall()

    def get_task(self, task_id: int, user_id: int) -> Optional[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)).fetchone()

    def add_task(
        self, user_id: int, subject_id: Optional[int], title: str, description: str, deadline: str, priority: str
    ) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                conn.execute(
                    """INSERT INTO tasks (user_id, subject_id, title, description, deadline, priority, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, subject_id, title.strip(), description.strip(), deadline, priority, datetime.now().isoformat(timespec="seconds")),
                )
            return True, "Task added successfully."
        except sqlite3.Error as error:
            return False, f"Could not save task: {error}"

    def update_task(
        self, task_id: int, user_id: int, subject_id: Optional[int], title: str, description: str, deadline: str, priority: str
    ) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                result = conn.execute(
                    """UPDATE tasks SET subject_id = ?, title = ?, description = ?, deadline = ?, priority = ?
                       WHERE id = ? AND user_id = ?""",
                    (subject_id, title.strip(), description.strip(), deadline, priority, task_id, user_id),
                )
            return (True, "Task updated successfully.") if result.rowcount else (False, "Task not found.")
        except sqlite3.Error as error:
            return False, f"Could not update task: {error}"

    def set_task_status(self, task_id: int, user_id: int, status: str) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                result = conn.execute(
                    "UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?", (status, task_id, user_id)
                )
            return (True, f"Task marked as {status.lower()}.") if result.rowcount else (False, "Task not found.")
        except sqlite3.Error as error:
            return False, f"Could not update task: {error}"

    def delete_task(self, task_id: int, user_id: int) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                result = conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            return (True, "Task deleted.") if result.rowcount else (False, "Task not found.")
        except sqlite3.Error as error:
            return False, f"Could not delete task: {error}"

    # --- Study session operations ---------------------------------------
    def get_study_sessions(self, user_id: int) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                """SELECT study_sessions.*, subjects.code AS subject_code, subjects.name AS subject_name
                   FROM study_sessions JOIN subjects ON study_sessions.subject_id = subjects.id
                   WHERE study_sessions.user_id = ? ORDER BY session_date DESC, study_sessions.id DESC""",
                (user_id,),
            ).fetchall()

    def add_study_session(
        self, user_id: int, subject_id: int, duration_minutes: int, session_date: str, notes: str
    ) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                conn.execute(
                    """INSERT INTO study_sessions (user_id, subject_id, duration_minutes, session_date, notes)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, subject_id, duration_minutes, session_date, notes.strip()),
                )
            return True, "Study session saved."
        except sqlite3.Error as error:
            return False, f"Could not save study session: {error}"

    def delete_study_session(self, session_id: int, user_id: int) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                result = conn.execute("DELETE FROM study_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
            return (True, "Study session deleted.") if result.rowcount else (False, "Session not found.")
        except sqlite3.Error as error:
            return False, f"Could not delete session: {error}"

    # --- Attendance operations ------------------------------------------
    def get_attendance(self, user_id: int) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                """SELECT attendance.*, subjects.code, subjects.name
                   FROM attendance JOIN subjects ON attendance.subject_id = subjects.id
                   WHERE attendance.user_id = ? ORDER BY subjects.code COLLATE NOCASE""",
                (user_id,),
            ).fetchall()

    def upsert_attendance(self, user_id: int, subject_id: int, total: int, attended: int) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                conn.execute(
                    """INSERT INTO attendance (user_id, subject_id, total_classes, attended_classes)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(user_id, subject_id) DO UPDATE SET
                       total_classes = excluded.total_classes, attended_classes = excluded.attended_classes""",
                    (user_id, subject_id, total, attended),
                )
            return True, "Attendance saved."
        except sqlite3.Error as error:
            return False, f"Could not save attendance: {error}"

    def delete_attendance(self, attendance_id: int, user_id: int) -> tuple[bool, str]:
        try:
            with self.connect() as conn:
                result = conn.execute("DELETE FROM attendance WHERE id = ? AND user_id = ?", (attendance_id, user_id))
            return (True, "Attendance record deleted.") if result.rowcount else (False, "Record not found.")
        except sqlite3.Error as error:
            return False, f"Could not delete attendance: {error}"

    # --- Dashboard, analytics and reports -------------------------------
    def get_dashboard_stats(self, user_id: int) -> dict[str, float | int]:
        with self.connect() as conn:
            subjects = conn.execute("SELECT COUNT(*) FROM subjects WHERE user_id = ?", (user_id,)).fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'Pending'", (user_id,)).fetchone()[0]
            completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'Completed'", (user_id,)).fetchone()[0]
            minutes = conn.execute("SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions WHERE user_id = ?", (user_id,)).fetchone()[0]
            attendance = conn.execute(
                "SELECT COALESCE(SUM(attended_classes) * 100.0 / NULLIF(SUM(total_classes), 0), 0) FROM attendance WHERE user_id = ?",
                (user_id,),
            ).fetchone()[0]
        return {"subjects": subjects, "pending": pending, "completed": completed, "study_hours": minutes / 60, "attendance": attendance}

    def get_analytics_data(self, user_id: int) -> dict[str, list[sqlite3.Row]]:
        with self.connect() as conn:
            study = conn.execute(
                """SELECT subjects.code, COALESCE(SUM(study_sessions.duration_minutes), 0) / 60.0 AS hours
                   FROM subjects LEFT JOIN study_sessions ON subjects.id = study_sessions.subject_id
                   WHERE subjects.user_id = ? GROUP BY subjects.id ORDER BY subjects.code""",
                (user_id,),
            ).fetchall()
            attendance = conn.execute(
                """SELECT subjects.code, attendance.id AS attendance_id,
                   COALESCE(attendance.attended_classes * 100.0 / NULLIF(attendance.total_classes, 0), 0) AS percentage
                   FROM subjects LEFT JOIN attendance ON subjects.id = attendance.subject_id
                   WHERE subjects.user_id = ? ORDER BY subjects.code""",
                (user_id,),
            ).fetchall()
            tasks = conn.execute(
                "SELECT status, COUNT(*) AS total FROM tasks WHERE user_id = ? GROUP BY status", (user_id,)
            ).fetchall()
        return {"study": study, "attendance": attendance, "tasks": tasks}

    def get_report_data(self, user_id: int) -> dict[str, object]:
        with self.connect() as conn:
            user = conn.execute("SELECT username, full_name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return {
            "user": user,
            "stats": self.get_dashboard_stats(user_id),
            "subjects": self.get_subjects(user_id),
            "attendance": self.get_attendance(user_id),
            "sessions": self.get_study_sessions(user_id),
            "tasks": self.get_tasks(user_id, "All"),
        }

    def insert_sample_data(self, user_id: int) -> tuple[bool, str]:
        """Insert a small, opt-in demo dataset once for the current user."""
        try:
            if self.get_subjects(user_id):
                return False, "Sample data is available only for a new account with no subjects."
            with self.connect() as conn:
                ids: dict[str, int] = {}
                for code, name, teacher in [
                    ("CS301", "Data Structures", "Dr. Mehta"),
                    ("MA201", "Discrete Mathematics", "Prof. Rao"),
                    ("EC205", "Digital Electronics", "Dr. Shah"),
                ]:
                    cursor = conn.execute("INSERT INTO subjects (user_id, code, name, teacher) VALUES (?, ?, ?, ?)", (user_id, code, name, teacher))
                    ids[code] = cursor.lastrowid
                today = date.today().isoformat()
                conn.executemany(
                    """INSERT INTO tasks (user_id, subject_id, title, description, deadline, priority, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    [
                        (user_id, ids["CS301"], "Linked list assignment", "Implement basic operations.", today, "High", "Pending", datetime.now().isoformat(timespec="seconds")),
                        (user_id, ids["MA201"], "Set theory worksheet", "Practice worksheet.", today, "Medium", "Completed", datetime.now().isoformat(timespec="seconds")),
                        (user_id, ids["EC205"], "Logic gates revision", "Prepare truth tables.", today, "Low", "Pending", datetime.now().isoformat(timespec="seconds")),
                    ],
                )
                conn.executemany(
                    "INSERT INTO study_sessions (user_id, subject_id, duration_minutes, session_date, notes) VALUES (?, ?, ?, ?, ?)",
                    [
                        (user_id, ids["CS301"], 120, today, "Arrays and linked lists"),
                        (user_id, ids["MA201"], 90, today, "Set operations"),
                        (user_id, ids["EC205"], 60, today, "Boolean algebra"),
                    ],
                )
                conn.executemany(
                    "INSERT INTO attendance (user_id, subject_id, total_classes, attended_classes) VALUES (?, ?, ?, ?)",
                    [(user_id, ids["CS301"], 20, 17), (user_id, ids["MA201"], 18, 15), (user_id, ids["EC205"], 16, 11)],
                )
            return True, "Sample data added. It can now be explored or edited."
        except sqlite3.Error as error:
            return False, f"Could not add sample data: {error}"
