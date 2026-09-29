from functools import wraps

from flask import flash, jsonify, redirect, session, url_for


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("main.index"))
            return f(*args, **kwargs)

        return decorated

    return decorator


def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated


def api_role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Authentication required"}), 401
            if session.get("role") not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)

        return decorated

    return decorator
