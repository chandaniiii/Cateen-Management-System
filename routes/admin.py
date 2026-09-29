from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func

from models import db
from models.category import Category
from models.menu_item import MenuItem
from models.order import Order
from models.review import Review
from models.user import User
from utils.decorators import api_login_required, api_role_required, login_required, role_required
from utils.helpers import save_upload

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _today_filter():
    today = datetime.now(timezone.utc).date()
    return func.date(Order.created_at) == today


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    total_users = User.query.filter_by(role="student").count()
    today_orders = Order.query.filter(_today_filter()).count()
    revenue_today = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(_today_filter(), Order.status == "completed")
        .scalar()
    )
    available_items = MenuItem.query.filter_by(is_available=True).filter(MenuItem.stock > 0).count()
    low_stock = MenuItem.query.filter(MenuItem.stock <= MenuItem.minimum_stock, MenuItem.stock > 0).count()
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        today_orders=today_orders,
        revenue_today=float(revenue_today),
        available_items=available_items,
        low_stock=low_stock,
    )


@admin_bp.route("/orders")
@login_required
@role_required("admin")
def orders():
    orders_list = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=orders_list)


@admin_bp.route("/menu")
@login_required
@role_required("admin")
def menu():
    items = MenuItem.query.order_by(MenuItem.name).all()
    categories = Category.query.all()
    return render_template("admin/menu.html", items=items, categories=categories)


@admin_bp.route("/menu/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_menu_item():
    categories = Category.query.all()
    if request.method == "POST":
        try:
            image_path = None
            if "image" in request.files:
                image_path = save_upload(request.files["image"])

            item = MenuItem(
                name=request.form.get("name", "").strip(),
                category_id=int(request.form.get("category_id")),
                description=request.form.get("description", "").strip(),
                price=float(request.form.get("price", 0)),
                image=image_path,
                stock=int(request.form.get("stock", 0)),
                minimum_stock=int(request.form.get("minimum_stock", 5)),
                is_available=request.form.get("is_available") == "on",
            )
            if item.stock <= 0:
                item.is_available = False
            db.session.add(item)
            db.session.commit()
            flash("Menu item added.", "success")
            return redirect(url_for("admin.menu"))
        except (ValueError, TypeError) as e:
            flash(f"Invalid input: {e}", "danger")

    return render_template("admin/menu_form.html", categories=categories, item=None)


@admin_bp.route("/menu/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    categories = Category.query.all()
    if request.method == "POST":
        try:
            if "image" in request.files and request.files["image"].filename:
                item.image = save_upload(request.files["image"]) or item.image

            item.name = request.form.get("name", item.name).strip()
            item.category_id = int(request.form.get("category_id"))
            item.description = request.form.get("description", "").strip()
            item.price = float(request.form.get("price"))
            item.stock = int(request.form.get("stock"))
            item.minimum_stock = int(request.form.get("minimum_stock"))
            item.is_available = request.form.get("is_available") == "on"
            if item.stock <= 0:
                item.is_available = False
            db.session.commit()
            flash("Menu item updated.", "success")
            return redirect(url_for("admin.menu"))
        except (ValueError, TypeError) as e:
            flash(f"Invalid input: {e}", "danger")

    return render_template("admin/menu_form.html", categories=categories, item=item)


@admin_bp.route("/menu/<int:item_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Menu item deleted.", "success")
    return redirect(url_for("admin.menu"))


@admin_bp.route("/categories")
@login_required
@role_required("admin")
def categories():
    cats = Category.query.all()
    return render_template("admin/categories.html", categories=cats)


@admin_bp.route("/categories/add", methods=["POST"])
@login_required
@role_required("admin")
def add_category():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not name:
        flash("Category name is required.", "danger")
    elif Category.query.filter_by(name=name).first():
        flash("Category already exists.", "danger")
    else:
        db.session.add(Category(name=name, description=description))
        db.session.commit()
        flash("Category added.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:cat_id>/edit", methods=["POST"])
@login_required
@role_required("admin")
def edit_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    cat.name = request.form.get("name", cat.name).strip()
    cat.description = request.form.get("description", "").strip()
    db.session.commit()
    flash("Category updated.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.menu_items:
        flash("Cannot delete category with menu items.", "danger")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash("Category deleted.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/inventory")
@login_required
@role_required("admin")
def inventory():
    items = MenuItem.query.order_by(MenuItem.stock.asc()).all()
    return render_template("admin/inventory.html", items=items)


@admin_bp.route("/inventory/<int:item_id>/update", methods=["POST"])
@login_required
@role_required("admin")
def update_inventory(item_id):
    item = MenuItem.query.get_or_404(item_id)
    try:
        item.stock = int(request.form.get("stock", item.stock))
        item.minimum_stock = int(request.form.get("minimum_stock", item.minimum_stock))
        item.is_available = request.form.get("is_available") == "on" and item.stock > 0
        db.session.commit()
        flash(f"Inventory updated for {item.name}.", "success")
    except (ValueError, TypeError):
        flash("Invalid stock values.", "danger")
    return redirect(url_for("admin.inventory"))


@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users_list)


@admin_bp.route("/users/<int:user_id>/update", methods=["POST"])
@login_required
@role_required("admin")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session["user_id"]:
        flash("You cannot modify your own account here.", "warning")
        return redirect(url_for("admin.users"))

    role = request.form.get("role")
    status = request.form.get("status")
    if role in ("student", "staff", "admin"):
        user.role = role
    if status in ("active", "inactive"):
        user.status = status
    db.session.commit()
    flash("User updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/staff")
@login_required
@role_required("admin")
def staff():
    staff_list = User.query.filter(User.role.in_(["staff", "admin"])).all()
    return render_template("admin/staff.html", staff_list=staff_list)


@admin_bp.route("/reviews")
@login_required
@role_required("admin")
def reviews():
    reviews_list = Review.query.order_by(Review.created_at.desc()).all()
    return render_template("admin/reviews.html", reviews=reviews_list)


@admin_bp.route("/reviews/<int:review_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_visible = not review.is_visible
    db.session.commit()
    flash("Review visibility updated.", "success")
    return redirect(url_for("admin.reviews"))


@admin_bp.route("/reports")
@login_required
@role_required("admin")
def reports():
    return render_template("admin/reports.html")


@admin_bp.route("/settings")
@login_required
@role_required("admin")
def settings():
    return render_template("admin/settings.html")


# --- API endpoints ---

@admin_bp.route("/api/reports")
@api_login_required
@api_role_required("admin")
def api_reports():
    today = datetime.now(timezone.utc).date()

    daily_sales = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        revenue = (
            db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
            .filter(func.date(Order.created_at) == day, Order.status == "completed")
            .scalar()
        )
        count = (
            Order.query.filter(func.date(Order.created_at) == day, Order.status == "completed").count()
        )
        daily_sales.append({"date": day.isoformat(), "revenue": float(revenue), "orders": count})

    weekly_orders = []
    for i in range(3, -1, -1):
        start = today - timedelta(days=(i + 1) * 7)
        end = today - timedelta(days=i * 7)
        count = Order.query.filter(
            func.date(Order.created_at) > start, func.date(Order.created_at) <= end
        ).count()
        weekly_orders.append({"week": f"Week {4 - i}", "orders": count})

    from models.order import OrderItem

    popular = (
        db.session.query(MenuItem.name, func.sum(OrderItem.quantity).label("qty"))
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .group_by(MenuItem.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(8)
        .all()
    )

    revenue_by_category = (
        db.session.query(Category.name, func.sum(OrderItem.price * OrderItem.quantity).label("rev"))
        .join(MenuItem, MenuItem.category_id == Category.id)
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status == "completed")
        .group_by(Category.id)
        .all()
    )

    return jsonify(
        {
            "daily_sales": daily_sales,
            "weekly_orders": weekly_orders,
            "popular_foods": [{"name": p[0], "quantity": int(p[1])} for p in popular],
            "revenue_by_category": [{"category": r[0], "revenue": float(r[1])} for r in revenue_by_category],
        }
    )


@admin_bp.route("/api/users")
@api_login_required
@api_role_required("admin")
def api_users():
    users_list = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users_list]})


@admin_bp.route("/api/inventory")
@api_login_required
@api_role_required("admin")
def api_inventory():
    items = MenuItem.query.all()
    return jsonify({"items": [i.to_dict() for i in items]})
