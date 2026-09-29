from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models import db
from models.user import User
from utils.decorators import login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.dashboard_redirect"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        student_id = request.form.get("student_id", "").strip()
        phone = request.form.get("phone", "").strip()

        errors = []
        if not name or len(name) < 2:
            errors.append("Name must be at least 2 characters.")
        if not email or "@" not in email:
            errors.append("Valid email is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("register.html")

        user = User(
            name=name,
            email=email,
            student_id=student_id or None,
            phone=phone or None,
            role="student",
            status="active",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.dashboard_redirect"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        if user.status != "active":
            flash("Your account is inactive. Contact admin.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id
        session["name"] = user.name
        session["email"] = user.email
        session["role"] = user.role
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for("main.dashboard_redirect"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
