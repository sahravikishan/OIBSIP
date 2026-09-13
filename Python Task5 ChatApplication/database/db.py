import os
import sqlite3
from typing import Optional, List, Dict, Any

DEFAULT_ROOMS = [
    ("General", "Open discussion for all participants", 1),
    ("Python Lounge", "Discussions, tips, and troubleshooting in Python", 1),
    ("Projects", "Share what you are building and collaborate", 1),
    ("Random", "Casual conversations, humor, and off-topic chat", 1)
]

def get_connection(db_path: str) -> sqlite3.Connection:
    """
    Establish and configure a thread-safe connection to SQLite.
    Enables foreign keys and returns dictionary-accessible rows.
    """
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
    conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    if db_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db(db_path: str) -> None:
    """
    Initialize SQLite database schema and seed default chat rooms.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        # Seed default rooms if none exist
        cursor = conn.cursor()
        for name, desc, is_def in DEFAULT_ROOMS:
            cursor.execute(
                "INSERT OR IGNORE INTO rooms (name, description, is_default) VALUES (?, ?, ?);",
                (name, desc, is_def)
            )
        conn.commit()

# --- User Queries ---

def create_user(db_path: str, username: str, password_hash: str) -> Optional[int]:
    """Insert a new user using parameterized SQL."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?);",
                (username.strip(), password_hash)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

def get_user_by_username(db_path: str, username: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by username."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE;", (username.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(db_path: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user record by primary key id."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# --- Room Queries ---

def get_all_rooms(db_path: str) -> List[Dict[str, Any]]:
    """Retrieve all available group chat rooms."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.id, r.name, r.description, r.is_default, r.room_type,
                   (CASE WHEN r.passcode_hash IS NOT NULL AND r.passcode_hash != '' THEN 1 ELSE 0 END) AS is_locked,
                   r.created_at,
                   u.username AS creator_name,
                   (SELECT COUNT(*) FROM messages m WHERE m.room_id = r.id) AS message_count
            FROM rooms r
            LEFT JOIN users u ON r.created_by = u.id
            WHERE r.room_type = 'group' OR r.room_type IS NULL
            ORDER BY r.is_default DESC, r.name ASC;
            """
        )
        return [dict(row) for row in cursor.fetchall()]

def get_room_by_id(db_path: str, room_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single room by its id with locked flag."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.id, r.name, r.description, r.is_default, r.room_type, r.passcode_hash,
                   (CASE WHEN r.passcode_hash IS NOT NULL AND r.passcode_hash != '' THEN 1 ELSE 0 END) AS is_locked,
                   r.created_by, r.created_at
            FROM rooms r
            WHERE r.id = ?;
            """,
            (room_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def get_room_by_name(db_path: str, room_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve a room by its name."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE name = ? COLLATE NOCASE;", (room_name.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_room(db_path: str, name: str, description: str = "", created_by: Optional[int] = None, passcode_hash: Optional[str] = None) -> Optional[int]:
    """Create a new group chat room with optional passcode."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO rooms (name, description, created_by, is_default, room_type, passcode_hash) VALUES (?, ?, ?, 0, 'group', ?);",
                (name.strip(), description.strip(), created_by, passcode_hash)
            )
            room_id = cursor.lastrowid
            if created_by:
                cursor.execute(
                    "INSERT OR IGNORE INTO room_members (room_id, user_id) VALUES (?, ?);",
                    (room_id, created_by)
                )
            conn.commit()
            return room_id
        except sqlite3.IntegrityError:
            return None

def get_all_users_directory(db_path: str, exclude_user_id: int) -> List[Dict[str, Any]]:
    """Retrieve all other registered users for starting direct conversations."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, created_at FROM users WHERE id != ? ORDER BY username ASC;",
            (exclude_user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_or_create_direct_room(db_path: str, user_a_id: int, user_b_id: int) -> Optional[Dict[str, Any]]:
    """
    Deterministically retrieve or create a private direct messaging room between two users.
    Ensures only user_a and user_b have access.
    """
    if user_a_id == user_b_id:
        return None

    # Deterministic room name key
    min_id, max_id = sorted([user_a_id, user_b_id])
    dm_name = f"dm_{min_id}_{max_id}"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE name = ? AND room_type = 'direct';", (dm_name,))
        row = cursor.fetchone()
        if row:
            room = dict(row)
        else:
            # Create the private DM room
            cursor.execute(
                "INSERT INTO rooms (name, description, is_default, room_type) VALUES (?, 'Direct Message', 0, 'direct');",
                (dm_name,)
            )
            room_id = cursor.lastrowid
            # Add both users as exclusive members
            cursor.execute("INSERT OR IGNORE INTO room_members (room_id, user_id) VALUES (?, ?);", (room_id, user_a_id))
            cursor.execute("INSERT OR IGNORE INTO room_members (room_id, user_id) VALUES (?, ?);", (room_id, user_b_id))
            conn.commit()
            cursor.execute("SELECT * FROM rooms WHERE id = ?;", (room_id,))
            room = dict(cursor.fetchone())

        return room

def get_user_direct_conversations(db_path: str, current_user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all direct message conversations that current_user is a member of,
    including the counterpart partner's username and unread/message count.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.id AS room_id, r.name AS raw_room_name,
                   u_partner.id AS partner_id,
                   u_partner.username AS partner_username,
                   (SELECT COUNT(*) FROM messages m WHERE m.room_id = r.id) AS message_count
            FROM rooms r
            JOIN room_members rm_self ON r.id = rm_self.room_id AND rm_self.user_id = ?
            JOIN room_members rm_partner ON r.id = rm_partner.room_id AND rm_partner.user_id != ?
            JOIN users u_partner ON rm_partner.user_id = u_partner.id
            WHERE r.room_type = 'direct'
            ORDER BY u_partner.username ASC;
            """,
            (current_user_id, current_user_id)
        )
        return [dict(row) for row in cursor.fetchall()]

def is_user_room_member(db_path: str, room_id: int, user_id: int) -> bool:
    """Check if user is explicitly recorded as member of a room."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM room_members WHERE room_id = ? AND user_id = ?;",
            (room_id, user_id)
        )
        return cursor.fetchone() is not None

def add_user_to_room(db_path: str, room_id: int, user_id: int) -> None:
    """Add user to room membership."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO room_members (room_id, user_id) VALUES (?, ?);",
            (room_id, user_id)
        )
        conn.commit()


# --- Message Queries ---

def save_message(db_path: str, room_id: int, user_id: int, content: str) -> Optional[Dict[str, Any]]:
    """
    Save a chat message to SQLite and return the created record with author username.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (room_id, user_id, content) VALUES (?, ?, ?);",
            (room_id, user_id, content)
        )
        msg_id = cursor.lastrowid
        conn.commit()

        # Fetch joined message representation
        cursor.execute(
            """
            SELECT m.id, m.room_id, m.user_id, m.content, m.created_at,
                   u.username, r.name AS room_name
            FROM messages m
            JOIN users u ON m.user_id = u.id
            JOIN rooms r ON m.room_id = r.id
            WHERE m.id = ?;
            """,
            (msg_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def get_room_messages(db_path: str, room_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve message history for a specific room in chronological order.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.room_id, m.user_id, m.content, m.created_at,
                   u.username
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.room_id = ?
            ORDER BY m.created_at ASC, m.id ASC
            LIMIT ?;
            """,
            (room_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
