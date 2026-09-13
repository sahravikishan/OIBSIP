import pytest
import os
import tempfile
from app import create_app
from config import TestingConfig
from utils.security import hash_password, verify_password, validate_username, validate_password
from database.db import get_user_by_username

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    class CustomTestConfig(TestingConfig):
        DATABASE_PATH = db_path
        TESTING = True
        WTF_CSRF_ENABLED = False

    app, socketio = create_app(CustomTestConfig)
    app.testing = True

    with app.test_client() as client:
        yield client, db_path

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass

def test_password_hashing():
    """Verify passwords are secure and not plain text."""
    plain = "SuperSecret123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert "pbkdf2:sha256" in hashed
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_username_validation():
    """Verify username requirements."""
    assert validate_username("alice")[0] is True
    assert validate_username("bob_123")[0] is True
    assert validate_username("ab")[0] is False  # too short
    assert validate_username("a" * 26)[0] is False  # too long
    assert validate_username("bad user")[0] is False  # spaces not allowed
    assert validate_username("bad<tag>")[0] is False  # xss chars not allowed

def test_registration_and_duplicate_rejection(client):
    """Verify user registration and duplicate prevention."""
    test_client, db_path = client

    # Register first user
    res = test_client.post("/register", json={
        "username": "chattester",
        "password": "password123",
        "confirm_password": "password123"
    })
    assert res.status_code in (200, 201)

    # Check user in DB
    user = get_user_by_username(db_path, "chattester")
    assert user is not None
    assert user["username"] == "chattester"
    assert user["password_hash"] != "password123"
    assert verify_password("password123", user["password_hash"]) is True

    # Logout so session is cleared before attempting duplicate registration
    test_client.get("/logout")

    # Attempt duplicate registration with same username
    res_dup = test_client.post("/register", json={
        "username": "chattester",
        "password": "newpassword123",
        "confirm_password": "newpassword123"
    })
    assert res_dup.status_code == 409
    data = res_dup.get_json()
    assert "already taken" in data["error"].lower()

def test_login_flow(client):
    """Verify login authentication and session creation."""
    test_client, _ = client

    # Register user
    test_client.post("/register", json={
        "username": "logintester",
        "password": "correct_password",
        "confirm_password": "correct_password"
    })

    # Clear session by logging out
    test_client.get("/logout")

    # Wrong password
    res_bad = test_client.post("/login", json={
        "username": "logintester",
        "password": "wrong_password"
    })
    assert res_bad.status_code == 401

    # Correct password
    res_ok = test_client.post("/login", json={
        "username": "logintester",
        "password": "correct_password"
    })
    assert res_ok.status_code == 200

    # Verify session
    res_me = test_client.get("/api/me")
    assert res_me.status_code == 200
    assert res_me.get_json()["user"]["username"] == "logintester"

def test_unauthenticated_chat_redirect(client):
    """Verify unauthenticated user cannot access chat page."""
    test_client, _ = client
    test_client.get("/logout")

    res = test_client.get("/chat", follow_redirects=False)
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]
