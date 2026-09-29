from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func

from models import db
from models.order import Order
from utils.decorators import api_login_required, api_role_required, login_required, role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

VALID_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["preparing", "cancelled"],
    "preparing": ["ready"],
    "ready": ["completed"],
}


def _today_filter():
    today = datetime.now(timezone.utc).date()
    return func.date(Order.created_at) == today


@staff_bp.route("/dashboard")
@login_required
@role_required("staff", "admin")
def dashboard():
    today_orders = Order.query.filter(_today_filter()).count()
    pending = Order.query.filter_by(status="pending").count()
    preparing = Order.query.filter_by(status="preparing").count()
    completed_today = Order.query.filter(_today_filter(), Order.status == "completed").count()
    revenue_today = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(_today_filter(), Order.status == "completed")
        .scalar()
    )
    recent = Order.query.order_by(Order.created_at.desc()).limit(20).all()
    return render_template(
        "staff/dashboard.html",
        today_orders=today_orders,
        pending=pending,
        preparing=preparing,
        completed_today=completed_today,
        revenue_today=float(revenue_today),
        orders=recent,
    )


@staff_bp.route("/orders")
@login_required
@role_required("staff", "admin")
def orders():
    status = request.args.get("status", "pending")
    if status == "all":
        orders_list = Order.query.order_by(Order.created_at.desc()).all()
    elif status == "new":
        orders_list = (
            Order.query.filter(Order.status.in_(["pending", "confirmed"]))
            .order_by(Order.created_at.desc())
            .all()
        )
    else:
        orders_list = Order.query.filter_by(status=status).order_by(Order.created_at.desc()).all()
    return render_template("staff/orders.html", orders=orders_list, current_status=status)


@staff_bp.route("/orders/<int:order_id>")
@login_required
@role_required("staff", "admin")
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("staff/order_detail.html", order=order)


@staff_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@role_required("staff", "admin")
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "").strip()

    allowed = VALID_TRANSITIONS.get(order.status, [])
    if new_status not in allowed and new_status != order.status:
        flash(f"Cannot change status from {order.status} to {new_status}.", "danger")
        return redirect(request.referrer or url_for("staff.orders"))

    if new_status == "cancelled":
        _restore_stock(order)

    order.status = new_status
    if new_status == "completed" and order.payment_method == "cash":
        order.payment_status = "completed"
    db.session.commit()
    flash(f"Order #{order.id} updated to {new_status}.", "success")
    return redirect(request.referrer or url_for("staff.orders"))


def _restore_stock(order):
    from models.menu_item import MenuItem

    for item in order.items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        if menu_item:
            menu_item.stock += item.quantity
            if menu_item.stock > 0:
                menu_item.is_available = True


@staff_bp.route("/api/orders/<int:order_id>/status", methods=["PUT"])
@api_login_required
@api_role_required("staff", "admin")
def api_update_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip()

    allowed = VALID_TRANSITIONS.get(order.status, [])
    if new_status not in allowed:
        return jsonify({"error": f"Invalid transition from {order.status} to {new_status}"}), 400

    if new_status == "cancelled":
        _restore_stock(order)

    order.status = new_status
    if new_status == "completed" and order.payment_method == "cash":
        order.payment_status = "completed"
    db.session.commit()
    return jsonify({"message": "Status updated", "order": order.to_dict()})
