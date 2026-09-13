import pytest
import os
import tempfile
from app import create_app
from config import TestingConfig
from utils.security import (
    validate_username,
    validate_password,
    validate_room_name,
    validate_message_content
)
from utils.emoji import parse_emoji
from database.db import create_user, get_room_by_name, save_message, get_room_messages

@pytest.fixture
def test_app_client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    class SecConfig(TestingConfig):
        DATABASE_PATH = db_path
        TESTING = True

    app, socketio = create_app(SecConfig)
    app.testing = True

    with app.test_client() as client:
        yield client, app, socketio, db_path

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass

def test_empty_and_whitespace_message_validation():
    """Empty or pure whitespace messages must be rejected."""
    assert validate_message_content("")[0] is False
    assert validate_message_content("   ")[0] is False
    assert validate_message_content("\n\t  ")[0] is False
    assert validate_message_content("Valid message")[0] is True

def test_excessively_long_message_validation():
    """Messages exceeding 2000 characters must be rejected."""
    long_msg = "a" * 2001
    assert validate_message_content(long_msg)[0] is False
    exact_msg = "a" * 2000
    assert validate_message_content(exact_msg)[0] is True

def test_room_name_validation():
    """Room names must meet length and character restrictions."""
    assert validate_room_name("General")[0] is True
    assert validate_room_name("Tech-Talk 2026")[0] is True
    assert validate_room_name("a")[0] is False  # too short
    assert validate_room_name("a" * 33)[0] is False  # too long
    assert validate_room_name("Room<script>")[0] is False  # invalid chars

def test_xss_content_safety(test_app_client):
    """Ensure XSS payloads are handled safely as plain text."""
    client, app, socketio, db_path = test_app_client

    user_id = create_user(db_path, "attacker", "pass123456")
    room = get_room_by_name(db_path, "General")

    xss_payload = "<script>alert('XSS')</script><img src=x onerror=alert(1)>"
    msg_record = save_message(db_path, room["id"], user_id, xss_payload)
    assert msg_record is not None

    # Retrieve from DB and verify intact storage
    history = get_room_messages(db_path, room["id"])
    saved_msg = next((m for m in history if m["id"] == msg_record["id"]), None)
    assert saved_msg is not None
    assert saved_msg["content"] == xss_payload
    # Note: DOM rendering in static/js/chat_ui.js assigns this to element.textContent,
    # ensuring browser treats it as plain text and NEVER executes it as HTML.

def test_socket_send_empty_message_rejected(test_app_client):
    """Empty message via socket emits error."""
    client, app, socketio, db_path = test_app_client
    u_id = create_user(db_path, "validuser", "pass123456")
    room = get_room_by_name(db_path, "General")

    with client.session_transaction() as sess:
        sess["user_id"] = u_id
        sess["username"] = "validuser"

    sock = socketio.test_client(app, flask_test_client=client)
    sock.emit("join_chat_room", {"room_id": room["id"]})
    sock.get_received()

    # Emit empty message
    sock.emit("send_message", {"room_id": room["id"], "content": "   "})
    events = sock.get_received()
    error_events = [e for e in events if e["name"] == "error"]
    assert len(error_events) >= 1
    assert "blank" in error_events[0]["args"][0]["message"].lower() or "empty" in error_events[0]["args"][0]["message"].lower()
