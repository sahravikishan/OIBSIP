import os
import tempfile
import pytest
from database.db import (
    init_db,
    create_user,
    create_room,
    get_all_rooms,
    get_room_by_name,
    save_message,
    get_room_messages
)
from utils.security import hash_password

@pytest.fixture
def temp_db():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    init_db(db_path)
    yield db_path
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass

def test_default_rooms_seeded(temp_db):
    """Verify default rooms are populated."""
    rooms = get_all_rooms(temp_db)
    names = [r["name"] for r in rooms]
    assert "General" in names
    assert "Python Lounge" in names
    assert "Projects" in names
    assert "Random" in names

def test_create_custom_room_and_duplicates(temp_db):
    """Verify room creation and duplicate name rejection."""
    user_id = create_user(temp_db, "roomowner", hash_password("pass123"))
    room_id = create_room(temp_db, "AI Discussion", "Talk about AI agents", created_by=user_id)
    assert room_id is not None

    room = get_room_by_name(temp_db, "AI Discussion")
    assert room is not None
    assert room["description"] == "Talk about AI agents"

    # Duplicate room
    dup_id = create_room(temp_db, "AI Discussion", "Another one")
    assert dup_id is None

def test_message_persistence_across_connections(temp_db):
    """Verify messages are stored in SQLite and persist across connections."""
    user_id = create_user(temp_db, "sender1", hash_password("pass123"))
    room = get_room_by_name(temp_db, "General")
    room_id = room["id"]

    # Save multiple messages
    msg1 = save_message(temp_db, room_id, user_id, "First message")
    msg2 = save_message(temp_db, room_id, user_id, "Second message")
    assert msg1 is not None
    assert msg2 is not None

    # Retrieve messages
    history = get_room_messages(temp_db, room_id)
    assert len(history) >= 2
    contents = [m["content"] for m in history]
    assert "First message" in contents
    assert "Second message" in contents
    # Check chronological ordering: First message before Second message
    assert contents.index("First message") < contents.index("Second message")

def test_direct_messaging_and_isolation(temp_db):
    """Verify direct message rooms are created with exact membership and isolated."""
    from database.db import (
        get_or_create_direct_room,
        get_all_users_directory,
        get_user_direct_conversations,
        is_user_room_member
    )
    u1 = create_user(temp_db, "userA", hash_password("pass123"))
    u2 = create_user(temp_db, "userB", hash_password("pass123"))
    u3 = create_user(temp_db, "userC", hash_password("pass123"))

    # Directory listing excludes caller
    dir_u1 = get_all_users_directory(temp_db, u1)
    usernames = [u["username"] for u in dir_u1]
    assert "userA" not in usernames
    assert "userB" in usernames
    assert "userC" in usernames

    # Create DM between u1 and u2
    dm_room = get_or_create_direct_room(temp_db, u1, u2)
    assert dm_room is not None
    dm_room_id = dm_room["id"]

    # Same DM retrieval returns existing room
    dm_room_2 = get_or_create_direct_room(temp_db, u2, u1)
    assert dm_room_2["id"] == dm_room_id

    # Check membership
    assert is_user_room_member(temp_db, dm_room_id, u1) is True
    assert is_user_room_member(temp_db, dm_room_id, u2) is True
    assert is_user_room_member(temp_db, dm_room_id, u3) is False

    # Direct conversations list
    convs_u1 = get_user_direct_conversations(temp_db, u1)
    assert len(convs_u1) == 1
    assert convs_u1[0]["partner_username"] == "userB"

def test_passcode_protected_rooms(temp_db):
    """Verify rooms with passcodes require correct passcode."""
    from database.db import get_room_by_id, add_user_to_room, is_user_room_member
    from utils.security import verify_password

    owner_id = create_user(temp_db, "roomowner2", hash_password("pass123"))
    guest_id = create_user(temp_db, "guestuser", hash_password("pass123"))

    p_hash = hash_password("secret99")
    room_id = create_room(temp_db, "VIP Lounge", "Secret club", created_by=owner_id, passcode_hash=p_hash)
    assert room_id is not None

    # Owner is automatically member
    assert is_user_room_member(temp_db, room_id, owner_id) is True
    assert is_user_room_member(temp_db, room_id, guest_id) is False

    # Check passcode verification
    room = get_room_by_id(temp_db, room_id)
    assert verify_password("wrongcode", room["passcode_hash"]) is False
    assert verify_password("secret99", room["passcode_hash"]) is True

    # Add guest after entering passcode
    add_user_to_room(temp_db, room_id, guest_id)
    assert is_user_room_member(temp_db, room_id, guest_id) is True


