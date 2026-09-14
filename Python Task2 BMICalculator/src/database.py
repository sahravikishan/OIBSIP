"""
Database Access Layer for BMI Calculator.

Manages persistent SQLite storage, relational schemas (users and bmi_records),
parameterized queries, foreign key constraints, and robust error handling.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class DatabaseError(Exception):
    """Custom exception raised when an SQLite database operation encounters an error."""
    pass


class DatabaseManager:
    """
    Manages SQLite connections and CRUD operations for users and BMI history.
    Guarantees true persistent storage anchored to the project directory.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.
        If db_path is not provided, defaults to an absolute path inside the project's
        'database/' folder, ensuring persistence across restarts and working directories.
        """
        if db_path is None:
            # Stable absolute path anchored to project directory
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            db_dir = os.path.join(base_dir, "database")
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.abspath(os.path.join(db_dir, "bmi_records.db"))
        else:
            self.db_path = os.path.abspath(db_path)
            parent = os.path.dirname(self.db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        print(f"[SQLite Database] Persistent database location: {self.db_path}")
        self._init_database()

    @contextmanager
    def _connection(self):
        """
        Context manager that opens a connection, enables foreign keys,
        and guarantees connection closure to prevent file lock issues on Windows.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
        except sqlite3.Error as err:
            raise DatabaseError(f"Database operation failed on '{self.db_path}': {err}") from err
        finally:
            if conn:
                conn.close()

    def _init_database(self) -> None:
        """
        Create tables and indexes if they do not already exist.
        DOES NOT delete or drop existing tables or records.
        """
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL COLLATE NOCASE,
            created_at TEXT NOT NULL
        );
        """

        create_records_table = """
        CREATE TABLE IF NOT EXISTS bmi_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            bmi REAL NOT NULL,
            category TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """

        create_index = """
        CREATE INDEX IF NOT EXISTS idx_bmi_records_user_id ON bmi_records(user_id);
        """

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_users_table)
            cursor.execute(create_records_table)
            cursor.execute(create_index)
            conn.commit()

    def get_or_create_user(self, name: str) -> Tuple[int, bool]:
        """
        Retrieve user ID by name, creating a new user record if they do not exist.

        Returns:
            Tuple[int, bool]: (user_id, created_flag)
        """
        cleaned_name = name.strip()
        if not cleaned_name:
            raise DatabaseError("User name cannot be empty.")

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE name = ? COLLATE NOCASE;", (cleaned_name,))
            row = cursor.fetchone()
            if row:
                return int(row["id"]), False

            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO users (name, created_at) VALUES (?, ?);",
                (cleaned_name, now_iso),
            )
            conn.commit()
            return int(cursor.lastrowid), True

    def get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user dictionary by name (case-insensitive) if they exist.
        Does NOT create a new user.
        """
        cleaned_name = name.strip()
        if not cleaned_name:
            return None

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at FROM users WHERE name = ? COLLATE NOCASE;", (cleaned_name,))
            row = cursor.fetchone()
            if row:
                return {"id": int(row["id"]), "name": row["name"], "created_at": row["created_at"]}
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Fetch all users alphabetically ordered by name.
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at FROM users ORDER BY name COLLATE NOCASE ASC;")
            rows = cursor.fetchall()
            return [{"id": row["id"], "name": row["name"], "created_at": row["created_at"]} for row in rows]

    def insert_record(
        self,
        user_id: int,
        weight: float,
        height: float,
        bmi: float,
        category: str,
        recorded_at: Optional[str] = None,
    ) -> int:
        """
        Insert a new BMI measurement record for the given user.
        Commits transaction to disk immediately.

        Returns:
            int: Inserted record ID.
        """
        if recorded_at is None:
            recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """
        INSERT INTO bmi_records (user_id, weight, height, bmi, category, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, weight, height, bmi, category, recorded_at))
            conn.commit()
            return int(cursor.lastrowid)

    def get_user_records(self, user_id: int, order_desc: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve all BMI records for a specific user from SQLite.

        Args:
            user_id: Target user's primary key ID.
            order_desc: If True, orders by recorded_at DESC (newest first, ideal for table view).
                        If False, orders ASC (ideal for chronological trend plotting).
        """
        direction = "DESC" if order_desc else "ASC"
        query = f"""
        SELECT id, user_id, weight, height, bmi, category, recorded_at
        FROM bmi_records
        WHERE user_id = ?
        ORDER BY recorded_at {direction}, id {direction};
        """
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "weight": row["weight"],
                    "height": row["height"],
                    "bmi": row["bmi"],
                    "category": row["category"],
                    "recorded_at": row["recorded_at"],
                }
                for row in rows
            ]

    def delete_record(self, record_id: int) -> bool:
        """
        Delete a specific BMI record by ID.
        """
        query = "DELETE FROM bmi_records WHERE id = ?;"
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user and their associated BMI records (cascaded).
        """
        query = "DELETE FROM users WHERE id = ?;"
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            conn.commit()
            return cursor.rowcount > 0
