from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func

from models import db
from models.menu_item import MenuItem
from models.order import Order, OrderItem
from models.review import Review
from utils.decorators import api_login_required, api_role_required, login_required, role_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_cart():
    return session.get("cart", {})


def save_cart(cart):
    session["cart"] = cart
    session.modified = True


def cart_count():
    return sum(get_cart().values())


@student_bp.context_processor
def inject_cart_count():
    return {"cart_count": cart_count()}


@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    user_id = session["user_id"]
    active_order = (
        Order.query.filter_by(user_id=user_id)
        .filter(Order.status.in_(["pending", "confirmed", "preparing", "ready"]))
        .order_by(Order.created_at.desc())
        .first()
    )
    total_orders = Order.query.filter_by(user_id=user_id).count()
    recent_orders = (
        Order.query.filter_by(user_id=user_id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )
    popular = (
        MenuItem.query.filter_by(is_available=True)
        .filter(MenuItem.stock > 0)
        .limit(4)
        .all()
    )
    favorite = _get_favorite_food(user_id)
    return render_template(
        "student/dashboard.html",
        active_order=active_order,
        total_orders=total_orders,
        recent_orders=recent_orders,
        popular=popular,
        favorite=favorite,
    )


def _get_favorite_food(user_id):
    result = (
        db.session.query(MenuItem, func.sum(OrderItem.quantity).label("total_qty"))
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .group_by(MenuItem.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .first()
    )
    return result[0] if result else None


@student_bp.route("/menu")
@login_required
@role_required("student")
def menu():
    categories = db.session.query(MenuItem.category_id).distinct().all()
    from models.category import Category

    cats = Category.query.all()
    return render_template("student/menu.html", categories=cats)


@student_bp.route("/menu/<int:item_id>")
@login_required
@role_required("student")
def food_detail(item_id):
    item = MenuItem.query.get_or_404(item_id)
    reviews = (
        Review.query.filter_by(menu_item_id=item_id, is_visible=True)
        .order_by(Review.created_at.desc())
        .limit(10)
        .all()
    )
    avg_rating = (
        db.session.query(func.avg(Review.rating))
        .filter_by(menu_item_id=item_id, is_visible=True)
        .scalar()
    )
    return render_template(
        "student/food_detail.html",
        item=item,
        reviews=reviews,
        avg_rating=round(float(avg_rating), 1) if avg_rating else None,
    )


@student_bp.route("/cart")
@login_required
@role_required("student")
def cart():
    cart_data = get_cart()
    items = []
    subtotal = 0
    for item_id, qty in cart_data.items():
        menu_item = MenuItem.query.get(int(item_id))
        if menu_item:
            line_total = float(menu_item.price) * qty
            subtotal += line_total
            items.append({"item": menu_item, "quantity": qty, "line_total": line_total})
    return render_template("student/cart.html", items=items, subtotal=subtotal, total=subtotal)


@student_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@role_required("student")
def checkout():
    cart_data = get_cart()
    if not cart_data:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("student.menu"))

    items = []
    subtotal = 0
    for item_id, qty in cart_data.items():
        menu_item = MenuItem.query.get(int(item_id))
        if not menu_item:
            continue
        if menu_item.stock < qty or not menu_item.is_available:
            flash(f"{menu_item.name} is not available in requested quantity.", "danger")
            return redirect(url_for("student.cart"))
        line_total = float(menu_item.price) * qty
        subtotal += line_total
        items.append({"item": menu_item, "quantity": qty, "line_total": line_total})

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("student.menu"))

    if request.method == "POST":
        from models.user import User

        user = User.query.get(session["user_id"])
        payment_method = request.form.get("payment_method", "cash")
        pickup_time = request.form.get("pickup_time", "ASAP")
        name = request.form.get("name", user.name).strip()
        student_id = request.form.get("student_id", user.student_id or "").strip()
        phone = request.form.get("phone", user.phone or "").strip()

        valid_payments = ("cash", "esewa", "khalti", "qr")
        if payment_method not in valid_payments:
            flash("Invalid payment method.", "danger")
            return render_template("student/checkout.html", items=items, subtotal=subtotal, total=subtotal)

        order = Order(
            user_id=user.id,
            total_amount=subtotal,
            status="pending",
            payment_method=payment_method,
            payment_status="completed" if payment_method != "cash" else "pending",
            pickup_time=pickup_time,
        )
        db.session.add(order)
        db.session.flush()

        for entry in items:
            menu_item = entry["item"]
            qty = entry["quantity"]
            menu_item.stock -= qty
            if menu_item.stock <= 0:
                menu_item.is_available = False
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=qty,
                    price=menu_item.price,
                )
            )

        db.session.commit()
        save_cart({})
        return redirect(url_for("student.order_confirmation", order_id=order.id))

    return render_template("student/checkout.html", items=items, subtotal=subtotal, total=subtotal)


@student_bp.route("/order/<int:order_id>/confirmation")
@login_required
@role_required("student")
def order_confirmation(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()
    return render_template("student/order_confirmation.html", order=order)


@student_bp.route("/orders")
@login_required
@role_required("student")
def orders():
    active = (
        Order.query.filter_by(user_id=session["user_id"])
        .filter(Order.status.in_(["pending", "confirmed", "preparing", "ready"]))
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("student/orders.html", orders=active)


@student_bp.route("/orders/history")
@login_required
@role_required("student")
def order_history():
    orders_list = (
        Order.query.filter_by(user_id=session["user_id"])
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("student/order_history.html", orders=orders_list)


@student_bp.route("/orders/<int:order_id>")
@login_required
@role_required("student")
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()
    can_review = order.status == "completed"
    user_reviews = (
        Review.query.filter_by(user_id=session["user_id"], order_id=order_id).all()
        if can_review
        else []
    )
    existing_reviews = {r.menu_item_id: r for r in user_reviews}
    return render_template(
        "student/order_detail.html",
        order=order,
        can_review=can_review,
        existing_reviews=existing_reviews,
    )


@student_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
@role_required("student")
def cancel_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()
    if order.status != "pending":
        flash("Only pending orders can be cancelled.", "warning")
        return redirect(url_for("student.order_detail", order_id=order.id))

    from routes.staff import _restore_stock
    _restore_stock(order)
    order.status = "cancelled"
    order.payment_status = "failed"
    db.session.commit()
    flash(f"Order #{order.id} has been cancelled and items returned to canteen stock.", "info")
    return redirect(url_for("student.orders"))


@student_bp.route("/orders/<int:order_id>/track")
@login_required
@role_required("student")
def track_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()
    return render_template("student/track_order.html", order=order)


@student_bp.route("/profile")
@login_required
@role_required("student")
def profile():
    from models.user import User

    user = User.query.get(session["user_id"])
    return render_template("student/profile.html", user=user)


# --- Cart API ---

@student_bp.route("/api/cart", methods=["GET"])
@api_login_required
@api_role_required("student")
def api_get_cart():
    cart_data = get_cart()
    items = []
    subtotal = 0
    for item_id, qty in cart_data.items():
        menu_item = MenuItem.query.get(int(item_id))
        if menu_item:
            line_total = float(menu_item.price) * qty
            subtotal += line_total
            items.append(
                {
                    "menu_item_id": menu_item.id,
                    "name": menu_item.name,
                    "price": float(menu_item.price),
                    "quantity": qty,
                    "line_total": line_total,
                    "image": menu_item.image or "/static/images/food-placeholder.jpg",
                }
            )
    return jsonify({"items": items, "subtotal": subtotal, "total": subtotal, "count": cart_count()})


@student_bp.route("/api/cart/add", methods=["POST"])
@api_login_required
@api_role_required("student")
def api_cart_add():
    data = request.get_json(silent=True) or {}
    item_id = str(data.get("menu_item_id", ""))
    quantity = int(data.get("quantity", 1))

    if quantity < 1:
        return jsonify({"error": "Invalid quantity"}), 400

    menu_item = MenuItem.query.get(item_id)
    if not menu_item:
        return jsonify({"error": "Item not found"}), 404
    if not menu_item.is_available or menu_item.stock <= 0:
        return jsonify({"error": "Item is out of stock"}), 400

    cart = get_cart()
    current = cart.get(item_id, 0)
    if current + quantity > menu_item.stock:
        return jsonify({"error": f"Only {menu_item.stock} available"}), 400

    cart[item_id] = current + quantity
    save_cart(cart)
    return jsonify({"message": "Added to cart", "count": cart_count()})


@student_bp.route("/api/cart/update", methods=["PUT"])
@api_login_required
@api_role_required("student")
def api_cart_update():
    data = request.get_json(silent=True) or {}
    item_id = str(data.get("menu_item_id", ""))
    quantity = int(data.get("quantity", 0))

    menu_item = MenuItem.query.get(item_id)
    if not menu_item:
        return jsonify({"error": "Item not found"}), 404

    cart = get_cart()
    if quantity <= 0:
        cart.pop(item_id, None)
    else:
        if quantity > menu_item.stock:
            return jsonify({"error": f"Only {menu_item.stock} available"}), 400
        cart[item_id] = quantity
    save_cart(cart)
    return jsonify({"message": "Cart updated", "count": cart_count()})


@student_bp.route("/api/cart/remove", methods=["DELETE"])
@api_login_required
@api_role_required("student")
def api_cart_remove():
    data = request.get_json(silent=True) or {}
    item_id = str(data.get("menu_item_id", ""))
    cart = get_cart()
    cart.pop(item_id, None)
    save_cart(cart)
    return jsonify({"message": "Item removed", "count": cart_count()})


@student_bp.route("/api/reviews", methods=["POST"])
@api_login_required
@api_role_required("student")
def api_add_review():
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    menu_item_id = data.get("menu_item_id")
    rating = int(data.get("rating", 0))
    comment = (data.get("comment") or "").strip()

    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be 1-5"}), 400

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()
    if not order or order.status != "completed":
        return jsonify({"error": "Can only review completed orders"}), 400

    existing = Review.query.filter_by(
        user_id=session["user_id"], menu_item_id=menu_item_id, order_id=order_id
    ).first()
    if existing:
        return jsonify({"error": "Already reviewed this item"}), 400

    review = Review(
        user_id=session["user_id"],
        menu_item_id=menu_item_id,
        order_id=order_id,
        rating=rating,
        comment=comment,
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"message": "Review submitted", "review": review.to_dict()})
