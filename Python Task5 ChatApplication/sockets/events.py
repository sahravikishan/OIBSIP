import datetime
from typing import Dict, Any, Optional, Set
from flask import session, request, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from database.db import get_room_by_id, get_room_messages, save_message, get_user_by_id, is_user_room_member
from utils.security import validate_message_content
from utils.emoji import parse_emoji

# Track active connections: sid -> {"user_id": int, "username": str, "room_id": Optional[int]}
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_online_users_in_room(room_id: int) -> list:
    """Return unique usernames of users currently joined in a room."""
    users = set()
    for sid, info in ACTIVE_SESSIONS.items():
        if info.get("room_id") == room_id:
            users.add(info.get("username"))
    return sorted(list(users))

def get_online_usernames() -> list:
    """Return list of all currently connected unique usernames across the app."""
    return sorted(list(set(info["username"] for info in ACTIVE_SESSIONS.values())))

def register_socket_events(socketio: SocketIO):
    """Register all Socket.IO real-time event handlers."""

    @socketio.on("connect")
    def handle_connect():
        """Validate authenticated session upon connection."""
        user_id = session.get("user_id")
        username = session.get("username")

        if not user_id or not username:
            # Reject unauthenticated WebSocket connection
            return False

        sid = request.sid
        ACTIVE_SESSIONS[sid] = {
            "user_id": user_id,
            "username": username,
            "room_id": None
        }
        # Join user's personal private room for notifications
        join_room(f"user_{user_id}")

        emit("connected", {"status": "success", "username": username})
        # Broadcast global online users update
        emit("global_presence_update", {"online_users": get_online_usernames()}, broadcast=True)

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle client disconnection gracefully."""
        sid = request.sid
        client = ACTIVE_SESSIONS.pop(sid, None)

        if client:
            user_id = client["user_id"]
            leave_room(f"user_{user_id}")

            if client.get("room_id"):
                room_id = client["room_id"]
                username = client["username"]
                room_channel = f"room_{room_id}"

                # Leave channel
                leave_room(room_channel)

                # System leave notification to room participants
                emit(
                    "system_message",
                    {
                        "room_id": room_id,
                        "type": "leave",
                        "content": f"{username} has left the room.",
                        "timestamp": datetime.datetime.now().strftime("%I:%M %p")
                    },
                    to=room_channel
                )

                # Update active participant list in room
                remaining_users = get_online_users_in_room(room_id)
                emit(
                    "room_users_update",
                    {"room_id": room_id, "users": remaining_users},
                    to=room_channel
                )

            # Broadcast global presence update
            emit("global_presence_update", {"online_users": get_online_usernames()}, broadcast=True)

    @socketio.on("join_chat_room")
    def handle_join_room(data):
        """User requests to join a specific chat room."""
        sid = request.sid
        client = ACTIVE_SESSIONS.get(sid)
        if not client:
            emit("error", {"message": "Session not authenticated."})
            return

        room_id = data.get("room_id")
        if not room_id:
            emit("error", {"message": "Missing room_id."})
            return

        try:
            room_id = int(room_id)
        except (ValueError, TypeError):
            emit("error", {"message": "Invalid room_id format."})
            return

        db_path = current_app.config["DATABASE_PATH"]
        room = get_room_by_id(db_path, room_id)
        if not room:
            emit("error", {"message": "Room does not exist."})
            return

        # Security check 1: Direct Message Room
        if room.get("room_type") == "direct":
            if not is_user_room_member(db_path, room_id, client["user_id"]):
                emit("error", {"message": "Access denied: This is a private direct conversation."})
                return

        # Security check 2: Protected Passcode Group
        if room.get("passcode_hash"):
            if not is_user_room_member(db_path, room_id, client["user_id"]):
                emit("error", {"message": "Passcode required to join this room.", "locked": True, "room_id": room_id})
                return

        previous_room_id = client.get("room_id")
        # If switching from another room, leave previous channel
        if previous_room_id and previous_room_id != room_id:
            prev_channel = f"room_{previous_room_id}"
            leave_room(prev_channel)
            emit(
                "system_message",
                {
                    "room_id": previous_room_id,
                    "type": "leave",
                    "content": f"{client['username']} has left the room.",
                    "timestamp": datetime.datetime.now().strftime("%I:%M %p")
                },
                to=prev_channel
            )
            # Update previous room users
            prev_users = get_online_users_in_room(previous_room_id)
            emit(
                "room_users_update",
                {"room_id": previous_room_id, "users": prev_users},
                to=prev_channel
            )

        # Update client's active room
        client["room_id"] = room_id
        new_channel = f"room_{room_id}"
        join_room(new_channel)

        # 1. Send room message history from SQLite to this user only
        history = get_room_messages(db_path, room_id, limit=100)
        formatted_history = []
        for msg in history:
            formatted_history.append({
                "id": msg["id"],
                "room_id": msg["room_id"],
                "user_id": msg["user_id"],
                "username": msg["username"],
                "content": parse_emoji(msg["content"]),
                "created_at": msg["created_at"]
            })

        emit("room_history", {
            "room_id": room_id,
            "room_name": room["name"],
            "description": room["description"],
            "room_type": room.get("room_type", "group"),
            "messages": formatted_history
        })

        # 2. System join message broadcast to room (only for public/group rooms)
        if room.get("room_type") != "direct":
            emit(
                "system_message",
                {
                    "room_id": room_id,
                    "type": "join",
                    "content": f"{client['username']} has joined the room.",
                    "timestamp": datetime.datetime.now().strftime("%I:%M %p")
                },
                to=new_channel
            )

        # 3. Broadcast updated online users in room
        current_users = get_online_users_in_room(room_id)
        emit(
            "room_users_update",
            {"room_id": room_id, "users": current_users},
            to=new_channel
        )

    @socketio.on("leave_chat_room")
    def handle_leave_room(data):
        """User explicitly leaves a chat room."""
        sid = request.sid
        client = ACTIVE_SESSIONS.get(sid)
        if not client or not client.get("room_id"):
            return

        room_id = client["room_id"]
        channel = f"room_{room_id}"
        leave_room(channel)
        client["room_id"] = None

        emit(
            "system_message",
            {
                "room_id": room_id,
                "type": "leave",
                "content": f"{client['username']} has left the room.",
                "timestamp": datetime.datetime.now().strftime("%I:%M %p")
            },
                to=channel
        )

        users = get_online_users_in_room(room_id)
        emit("room_users_update", {"room_id": room_id, "users": users}, to=channel)

    @socketio.on("send_message")
    def handle_send_message(data):
        """
        Validate, parse emoji shortcodes, persist to SQLite,
        and broadcast real-time message to room participants.
        """
        sid = request.sid
        client = ACTIVE_SESSIONS.get(sid)
        if not client:
            emit("error", {"message": "Unauthenticated user."})
            return

        room_id = data.get("room_id")
        content = data.get("content")

        if not room_id or not content:
            emit("error", {"message": "Room ID and message content are required."})
            return

        try:
            room_id = int(room_id)
        except (ValueError, TypeError):
            emit("error", {"message": "Invalid room_id."})
            return

        # Validate content
        valid, err = validate_message_content(content)
        if not valid:
            emit("error", {"message": err})
            return

        db_path = current_app.config["DATABASE_PATH"]
        room = get_room_by_id(db_path, room_id)
        if not room:
            emit("error", {"message": "Room not found."})
            return

        # If direct room, verify membership
        if room.get("room_type") == "direct":
            if not is_user_room_member(db_path, room_id, client["user_id"]):
                emit("error", {"message": "Access denied: You are not a member of this conversation."})
                return

        # If protected room, verify passcode membership
        if room.get("passcode_hash"):
            if not is_user_room_member(db_path, room_id, client["user_id"]):
                emit("error", {"message": "Passcode required to send messages in this room."})
                return

        # Ensure user is joined to the socket channel (handles reconnection seamlessly)
        if client.get("room_id") != room_id:
            client["room_id"] = room_id
            join_room(f"room_{room_id}")

        # Replace emoji shortcodes
        parsed_content = parse_emoji(content)

        # Save to SQLite database
        msg_record = save_message(
            db_path=db_path,
            room_id=room_id,
            user_id=client["user_id"],
            content=parsed_content
        )

        if not msg_record:
            emit("error", {"message": "Failed to save message."})
            return

        channel = f"room_{room_id}"
        payload = {
            "id": msg_record["id"],
            "room_id": room_id,
            "user_id": client["user_id"],
            "username": client["username"],
            "content": parsed_content,
            "created_at": msg_record["created_at"]
        }

        # Broadcast to room channel (including sender)
        emit("new_message", payload, to=channel)

        # If direct room, notify the counterpart user if they are not actively inside this room
        if room.get("room_type") == "direct":
            with get_room_by_id.__globals__["get_connection"](db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT user_id FROM room_members WHERE room_id = ? AND user_id != ?;",
                    (room_id, client["user_id"])
                )
                partner_row = cur.fetchone()
                if partner_row:
                    partner_uid = partner_row[0]
                    # Emit personal notification event to partner's user channel
                    emit(
                        "direct_message_alert",
                        {
                            "room_id": room_id,
                            "sender_id": client["user_id"],
                            "sender_username": client["username"],
                            "preview": parsed_content[:60]
                        },
                        to=f"user_{partner_uid}"
                    )

    @socketio.on("typing")
    def handle_typing(data):
        """Relay typing indicator to other room members."""
        sid = request.sid
        client = ACTIVE_SESSIONS.get(sid)
        if not client or not client.get("room_id"):
            return

        room_id = client["room_id"]
        is_typing = bool(data.get("is_typing", False))
        channel = f"room_{room_id}"

        # Broadcast to all in channel EXCEPT sender
        emit(
            "user_typing",
            {
                "username": client["username"],
                "room_id": room_id,
                "is_typing": is_typing
            },
            to=channel,
            include_self=False
        )

