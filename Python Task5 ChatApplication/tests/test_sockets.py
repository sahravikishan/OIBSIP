import pytest
import os
import tempfile
from app import create_app
from config import TestingConfig
from utils.security import hash_password
from database.db import create_user, get_room_by_name, get_all_rooms
from utils.emoji import parse_emoji

@pytest.fixture
def chat_env():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    class SocketsTestConfig(TestingConfig):
        DATABASE_PATH = db_path
        TESTING = True

    app, socketio = create_app(SocketsTestConfig)
    app.testing = True

    # Seed users
    u1_id = create_user(db_path, "alice", hash_password("alicepass123"))
    u2_id = create_user(db_path, "bob", hash_password("bobpass123"))

    rooms = get_all_rooms(db_path)
    general_room = get_room_by_name(db_path, "General")
    python_room = get_room_by_name(db_path, "Python Lounge")

    yield {
        "app": app,
        "socketio": socketio,
        "db_path": db_path,
        "alice_id": u1_id,
        "bob_id": u2_id,
        "general_id": general_room["id"],
        "python_id": python_room["id"]
    }

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass

def test_unauthenticated_socket_connection_rejected(chat_env):
    """Ensure socket connection without session is rejected."""
    app = chat_env["app"]
    socketio = chat_env["socketio"]

    client = socketio.test_client(app)
    # Since no session is set, connect handler returns False
    assert not client.is_connected()

def test_authenticated_socket_flow_and_two_way_messaging(chat_env):
    """Test two connected users in the same room exchange messages in real time."""
    app = chat_env["app"]
    socketio = chat_env["socketio"]
    gen_id = chat_env["general_id"]

    # Connect Alice
    with app.test_client() as flask_client_alice:
        with flask_client_alice.session_transaction() as sess:
            sess["user_id"] = chat_env["alice_id"]
            sess["username"] = "alice"

        alice_socket = socketio.test_client(app, flask_test_client=flask_client_alice)
        assert alice_socket.is_connected()

        # Connect Bob
        with app.test_client() as flask_client_bob:
            with flask_client_bob.session_transaction() as sess:
                sess["user_id"] = chat_env["bob_id"]
                sess["username"] = "bob"

            bob_socket = socketio.test_client(app, flask_test_client=flask_client_bob)
            assert bob_socket.is_connected()

            # Alice joins General
            alice_socket.emit("join_chat_room", {"room_id": gen_id})
            alice_received = alice_socket.get_received()
            event_names = [e["name"] for e in alice_received]
            assert "room_history" in event_names
            assert "system_message" in event_names

            # Bob joins General
            bob_socket.emit("join_chat_room", {"room_id": gen_id})
            bob_received = bob_socket.get_received()
            # Alice should receive Bob's join system message
            alice_new_events = alice_socket.get_received()
            join_events = [e for e in alice_new_events if e["name"] == "system_message"]
            assert any("bob has joined" in j["args"][0]["content"].lower() for j in join_events)

            # Alice sends message: "Hello Bob :smile:"
            alice_socket.emit("send_message", {
                "room_id": gen_id,
                "content": "Hello Bob :smile:"
            })

            # Bob receives real-time message with parsed emoji and timestamp
            bob_events = bob_socket.get_received()
            msg_events = [e for e in bob_events if e["name"] == "new_message"]
            assert len(msg_events) >= 1
            received_msg = msg_events[0]["args"][0]
            assert received_msg["username"] == "alice"
            assert "Hello Bob 😄" in received_msg["content"]
            assert "created_at" in received_msg

            # Drain Alice's pending received events (which includes her own broadcasted message)
            alice_socket.get_received()

            # Bob replies: "Hi Alice :thumbsup:"
            bob_socket.emit("send_message", {
                "room_id": gen_id,
                "content": "Hi Alice :thumbsup:"
            })

            # Alice immediately receives Bob's message
            alice_events_2 = alice_socket.get_received()
            bob_reply_events = [e for e in alice_events_2 if e["name"] == "new_message"]
            assert len(bob_reply_events) >= 1
            reply_data = bob_reply_events[0]["args"][0]
            assert reply_data["username"] == "bob"
            assert "Hi Alice 👍" in reply_data["content"]

            # Bob disconnects -> Alice receives system leave notification
            bob_socket.disconnect()
            alice_events_3 = alice_socket.get_received()
            leave_events = [e for e in alice_events_3 if e["name"] == "system_message"]
            assert any("bob has left" in l["args"][0]["content"].lower() for l in leave_events)

def test_room_message_isolation(chat_env):
    """Messages in room A must not leak into room B."""
    app = chat_env["app"]
    socketio = chat_env["socketio"]
    gen_id = chat_env["general_id"]
    python_id = chat_env["python_id"]

    # Alice in General
    with app.test_client() as fc_alice:
        with fc_alice.session_transaction() as s:
            s["user_id"] = chat_env["alice_id"]
            s["username"] = "alice"
        alice_socket = socketio.test_client(app, flask_test_client=fc_alice)
        alice_socket.emit("join_chat_room", {"room_id": gen_id})
        alice_socket.get_received()

        # Bob in Python Lounge
        with app.test_client() as fc_bob:
            with fc_bob.session_transaction() as s:
                s["user_id"] = chat_env["bob_id"]
                s["username"] = "bob"
            bob_socket = socketio.test_client(app, flask_test_client=fc_bob)
            bob_socket.emit("join_chat_room", {"room_id": python_id})
            bob_socket.get_received()

            # Alice sends message to General
            alice_socket.emit("send_message", {
                "room_id": gen_id,
                "content": "Secret General Chat"
            })

            # Bob should NOT receive it
            bob_events = bob_socket.get_received()
            msg_events = [e for e in bob_events if e["name"] == "new_message"]
            assert len(msg_events) == 0

def test_emoji_shortcodes_and_unknown_handling():
    """Verify emoji parsing and unknown shortcode preservation."""
    assert parse_emoji("Great work :thumbsup: :fire:") == "Great work 👍 🔥"
    assert parse_emoji("Loving this :heart: and :rocket:") == "Loving this ❤️ and 🚀"
    assert parse_emoji("Unknown :not_an_emoji: here") == "Unknown :not_an_emoji: here"
