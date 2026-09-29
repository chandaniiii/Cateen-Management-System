from flask import Blueprint, jsonify, request, session

from models import db
from models.category import Category
from models.menu_item import MenuItem
from models.order import Order
from utils.decorators import api_login_required, api_role_required
from utils.helpers import save_upload

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/menu")
def get_menu():
    category_id = request.args.get("category_id")
    search = request.args.get("search", "").strip().lower()

    query = MenuItem.query.filter_by(is_available=True).filter(MenuItem.stock > 0)
    if category_id:
        query = query.filter_by(category_id=int(category_id))
    if search:
        query = query.filter(
            db.or_(MenuItem.name.ilike(f"%{search}%"), MenuItem.description.ilike(f"%{search}%"))
        )

    items = query.order_by(MenuItem.name).all()
    categories = Category.query.all()
    return jsonify(
        {
            "items": [i.to_dict() for i in items],
            "categories": [c.to_dict() for c in categories],
        }
    )


@api_bp.route("/menu/<int:item_id>")
def get_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    return jsonify(item.to_dict())


@api_bp.route("/menu", methods=["POST"])
@api_login_required
@api_role_required("admin")
def create_menu_item():
    data = request.get_json(silent=True) or {}
    try:
        item = MenuItem(
            name=data["name"],
            category_id=int(data["category_id"]),
            description=data.get("description", ""),
            price=float(data["price"]),
            stock=int(data.get("stock", 0)),
            minimum_stock=int(data.get("minimum_stock", 5)),
            is_available=data.get("is_available", True),
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/menu/<int:item_id>", methods=["PUT"])
@api_login_required
@api_role_required("admin")
def update_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    data = request.get_json(silent=True) or {}
    try:
        if "name" in data:
            item.name = data["name"]
        if "category_id" in data:
            item.category_id = int(data["category_id"])
        if "description" in data:
            item.description = data["description"]
        if "price" in data:
            item.price = float(data["price"])
        if "stock" in data:
            item.stock = int(data["stock"])
        if "minimum_stock" in data:
            item.minimum_stock = int(data["minimum_stock"])
        if "is_available" in data:
            item.is_available = bool(data["is_available"])
        db.session.commit()
        return jsonify(item.to_dict())
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/menu/<int:item_id>", methods=["DELETE"])
@api_login_required
@api_role_required("admin")
def delete_menu_item_api(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Deleted"})


@api_bp.route("/orders", methods=["GET"])
@api_login_required
def get_orders():
    role = session.get("role")
    if role == "student":
        orders = Order.query.filter_by(user_id=session["user_id"]).order_by(Order.created_at.desc()).all()
    elif role in ("staff", "admin"):
        status = request.args.get("status")
        query = Order.query
        if status:
            query = query.filter_by(status=status)
        orders = query.order_by(Order.created_at.desc()).all()
    else:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({"orders": [o.to_dict(include_user=role in ("staff", "admin")) for o in orders]})


@api_bp.route("/orders/<int:order_id>")
@api_login_required
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    role = session.get("role")
    if role == "student" and order.user_id != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(order.to_dict(include_user=role in ("staff", "admin")))


@api_bp.route("/orders/<int:order_id>/status", methods=["PUT"])
@api_login_required
@api_role_required("staff", "admin")
def update_order_status(order_id):
    from routes.staff import VALID_TRANSITIONS, _restore_stock

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
