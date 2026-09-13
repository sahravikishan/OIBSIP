from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from database.db import (
    get_all_rooms, get_room_by_id, get_room_by_name, create_room,
    get_room_messages, get_user_by_id, get_all_users_directory,
    get_or_create_direct_room, get_user_direct_conversations,
    is_user_room_member, add_user_to_room
)
from utils.security import validate_room_name, validate_room_passcode, hash_password, verify_password
from utils.emoji import get_emoji_catalog

chat_bp = Blueprint("chat", __name__)

def login_required(func):
    """Decorator to require authenticated session."""
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@chat_bp.route("/")
def index():
    """Root redirector."""
    if "user_id" in session:
        return redirect(url_for("chat.chat_view"))
    return redirect(url_for("auth.login"))

@chat_bp.route("/chat")
@login_required
def chat_view():
    """Main Chat application interface."""
    db_path = current_app.config["DATABASE_PATH"]
    current_uid = session["user_id"]
    user = get_user_by_id(db_path, current_uid)
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    rooms = get_all_rooms(db_path)
    direct_conversations = get_user_direct_conversations(db_path, current_uid)
    emojis = get_emoji_catalog()
    return render_template(
        "chat.html",
        current_user=user,
        rooms=rooms,
        direct_conversations=direct_conversations,
        emojis=emojis
    )

@chat_bp.route("/api/rooms", methods=["GET"])
def list_rooms():
    """API endpoint to list all available group chat rooms."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db_path = current_app.config["DATABASE_PATH"]
    rooms = get_all_rooms(db_path)
    return jsonify({"success": True, "rooms": rooms})

@chat_bp.route("/api/rooms", methods=["POST"])
def new_room():
    """API endpoint to create a new group chat room with optional passcode."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    passcode = (data.get("passcode") or "").strip()

    valid, err = validate_room_name(name)
    if not valid:
        return jsonify({"success": False, "error": err}), 400

    if passcode:
        valid_pc, pc_err = validate_room_passcode(passcode)
        if not valid_pc:
            return jsonify({"success": False, "error": pc_err}), 400
        passcode_hash = hash_password(passcode)
    else:
        passcode_hash = None

    db_path = current_app.config["DATABASE_PATH"]
    existing = get_room_by_name(db_path, name)
    if existing:
        return jsonify({"success": False, "error": f"A room named '{name}' already exists."}), 409

    room_id = create_room(db_path, name, description, created_by=session["user_id"], passcode_hash=passcode_hash)
    if not room_id:
        return jsonify({"success": False, "error": "Database error creating room."}), 500

    room = get_room_by_id(db_path, room_id)
    return jsonify({"success": True, "room": room}), 201

@chat_bp.route("/api/rooms/unlock", methods=["POST"])
def unlock_room():
    """Verify passcode for protected room and record membership."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    room_id = data.get("room_id")
    passcode = (data.get("passcode") or "").strip()

    if not room_id:
        return jsonify({"success": False, "error": "Missing room_id."}), 400

    db_path = current_app.config["DATABASE_PATH"]
    room = get_room_by_id(db_path, int(room_id))
    if not room:
        return jsonify({"success": False, "error": "Room not found."}), 404

    # If room is locked, check passcode
    if room.get("passcode_hash"):
        if not verify_password(passcode, room["passcode_hash"]):
            return jsonify({"success": False, "error": "Incorrect room passcode. Please try again."}), 403

    # Add user to membership
    add_user_to_room(db_path, int(room_id), session["user_id"])
    return jsonify({"success": True, "room": room})

@chat_bp.route("/api/direct/conversations", methods=["GET"])
def list_direct_conversations():
    """List all active direct messaging conversations for the current user."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db_path = current_app.config["DATABASE_PATH"]
    convs = get_user_direct_conversations(db_path, session["user_id"])
    return jsonify({"success": True, "conversations": convs})

@chat_bp.route("/api/direct/start", methods=["POST"])
def start_direct_message():
    """Start or open a direct message conversation with a specific user."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    target_user_id = data.get("user_id")
    if not target_user_id:
        return jsonify({"success": False, "error": "Missing target user_id."}), 400

    try:
        target_user_id = int(target_user_id)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid user_id."}), 400

    if target_user_id == session["user_id"]:
        return jsonify({"success": False, "error": "Cannot start direct message with yourself."}), 400

    db_path = current_app.config["DATABASE_PATH"]
    target_user = get_user_by_id(db_path, target_user_id)
    if not target_user:
        return jsonify({"success": False, "error": "User not found."}), 404

    room = get_or_create_direct_room(db_path, session["user_id"], target_user_id)
    if not room:
        return jsonify({"success": False, "error": "Could not create direct conversation."}), 500

    return jsonify({
        "success": True,
        "room_id": room["id"],
        "partner_id": target_user["id"],
        "partner_username": target_user["username"]
    })

@chat_bp.route("/api/users/directory", methods=["GET"])
def users_directory():
    """Return all registered users for starting a personal chat."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db_path = current_app.config["DATABASE_PATH"]
    users = get_all_users_directory(db_path, session["user_id"])
    return jsonify({"success": True, "users": users})

@chat_bp.route("/api/rooms/<int:room_id>/messages", methods=["GET"])
def room_messages(room_id: int):
    """API endpoint to fetch message history for a room with access verification."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db_path = current_app.config["DATABASE_PATH"]
    room = get_room_by_id(db_path, room_id)
    if not room:
        return jsonify({"success": False, "error": "Room not found."}), 404

    current_uid = session["user_id"]

    # Security check for direct rooms
    if room.get("room_type") == "direct":
        if not is_user_room_member(db_path, room_id, current_uid):
            return jsonify({"success": False, "error": "Access denied: Private direct message."}), 403

    # Security check for passcode protected group rooms
    if room.get("passcode_hash"):
        if not is_user_room_member(db_path, room_id, current_uid):
            return jsonify({"success": False, "error": "Passcode required to view messages.", "locked": True}), 403

    messages = get_room_messages(db_path, room_id, limit=100)
    return jsonify({
        "success": True,
        "room": room,
        "messages": messages
    })

@chat_bp.route("/api/emojis", methods=["GET"])
def emojis_list():
    """API endpoint returning emoji catalog."""
    return jsonify({"emojis": get_emoji_catalog()})

