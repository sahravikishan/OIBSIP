from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, current_app
from database.db import create_user, get_user_by_username, get_user_by_id
from utils.security import hash_password, verify_password, validate_username, validate_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if "user_id" in session:
        return redirect(url_for("chat.chat_view"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        confirm_password = data.get("confirm_password") or ""

        # Validation
        valid, err = validate_username(username)
        if not valid:
            if request.is_json:
                return jsonify({"success": False, "error": err}), 400
            flash(err, "danger")
            return render_template("auth.html", mode="register", username=username)

        valid_pw, pw_err = validate_password(password)
        if not valid_pw:
            if request.is_json:
                return jsonify({"success": False, "error": pw_err}), 400
            flash(pw_err, "danger")
            return render_template("auth.html", mode="register", username=username)

        if confirm_password and password != confirm_password:
            msg = "Passwords do not match."
            if request.is_json:
                return jsonify({"success": False, "error": msg}), 400
            flash(msg, "danger")
            return render_template("auth.html", mode="register", username=username)

        db_path = current_app.config["DATABASE_PATH"]

        # Duplicate username check
        existing = get_user_by_username(db_path, username)
        if existing:
            msg = f"Username '{username}' is already taken. Please choose another."
            if request.is_json:
                return jsonify({"success": False, "error": msg}), 409
            flash(msg, "danger")
            return render_template("auth.html", mode="register", username=username)

        # Hash and store
        p_hash = hash_password(password)
        user_id = create_user(db_path, username, p_hash)
        if not user_id:
            msg = "Failed to create account due to a database error. Please try again."
            if request.is_json:
                return jsonify({"success": False, "error": msg}), 500
            flash(msg, "danger")
            return render_template("auth.html", mode="register", username=username)

        # Auto-login after successful registration
        session.clear()
        session["user_id"] = user_id
        session["username"] = username

        if request.is_json:
            return jsonify({"success": True, "redirect": url_for("chat.chat_view")}), 201
        
        flash("Registration successful! Welcome to the chat.", "success")
        return redirect(url_for("chat.chat_view"))

    return render_template("auth.html", mode="register")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user authentication and session creation."""
    if "user_id" in session:
        return redirect(url_for("chat.chat_view"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            msg = "Please provide both username and password."
            if request.is_json:
                return jsonify({"success": False, "error": msg}), 400
            flash(msg, "danger")
            return render_template("auth.html", mode="login", username=username)

        db_path = current_app.config["DATABASE_PATH"]
        user = get_user_by_username(db_path, username)

        if not user or not verify_password(password, user["password_hash"]):
            msg = "Invalid username or password. Please try again."
            if request.is_json:
                return jsonify({"success": False, "error": msg}), 401
            flash(msg, "danger")
            return render_template("auth.html", mode="login", username=username)

        # Create authenticated session
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        if request.is_json:
            return jsonify({"success": True, "redirect": url_for("chat.chat_view")}), 200

        flash(f"Welcome back, {user['username']}!", "success")
        return redirect(url_for("chat.chat_view"))

    return render_template("auth.html", mode="login")

@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Clear session and redirect to login."""
    session.clear()
    if request.is_json:
        return jsonify({"success": True, "redirect": url_for("auth.login")})
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/api/me", methods=["GET"])
def me():
    """API endpoint to get current authenticated user."""
    if "user_id" not in session:
        return jsonify({"authenticated": False, "user": None}), 401
    
    db_path = current_app.config["DATABASE_PATH"]
    user = get_user_by_id(db_path, session["user_id"])
    if not user:
        session.clear()
        return jsonify({"authenticated": False, "user": None}), 401
        
    return jsonify({
        "authenticated": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"]
        }
    })
