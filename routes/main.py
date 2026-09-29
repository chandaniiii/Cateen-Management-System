from flask import Blueprint, redirect, render_template, session, url_for

from models.category import Category
from models.menu_item import MenuItem
from models.order import Order
from models.review import Review
from sqlalchemy import func

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    popular = (
        MenuItem.query.filter_by(is_available=True)
        .filter(MenuItem.stock > 0)
        .order_by(MenuItem.id)
        .limit(6)
        .all()
    )
    categories = Category.query.all()
    return render_template("index.html", popular=popular, categories=categories)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/dashboard")
def dashboard_redirect():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "staff":
        return redirect(url_for("staff.dashboard"))
    return redirect(url_for("student.dashboard"))
