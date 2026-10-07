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
    from config import Config
    from services.cart_manager import CartManager

    cart_data = get_cart()
    manager = CartManager(cart_data)
    items = []
    subtotal = 0.0

    for cart_item in manager.get_cart_items():
        items.append({
            "item": cart_item.menu_item,
            "quantity": cart_item.quantity,
            "line_total": cart_item.line_total,
        })
        subtotal += cart_item.line_total

    delivery_charge = manager.get_delivery_charge("delivery") if items else 0.0
    total = subtotal + delivery_charge

    return render_template(
        "student/cart.html",
        items=items,
        subtotal=subtotal,
        delivery_charge=delivery_charge,
        total=total,
        free_delivery_threshold=Config.FREE_DELIVERY_THRESHOLD,
    )


@student_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@role_required("student")
def checkout():
    from config import Config
    from models.user import User
    from services.cart_manager import CartManager
    from services.payment_processor import EsewaPaymentHandler

    user = User.query.get(session["user_id"])
    cart_data = get_cart()
    if not cart_data:
        flash("Your cart is empty. Please add delicious food items before checkout.", "warning")
        return redirect(url_for("student.menu"))

    manager = CartManager(cart_data)
    try:
        cart_items = manager.validate_for_checkout()
    except ValueError as err:
        flash(str(err), "danger")
        return redirect(url_for("student.cart"))

    items = []
    subtotal = 0.0
    for cart_item in cart_items:
        items.append({
            "item": cart_item.menu_item,
            "quantity": cart_item.quantity,
            "line_total": cart_item.line_total,
        })
        subtotal += cart_item.line_total

    default_delivery_charge = manager.get_delivery_charge("delivery")
    default_total = subtotal + default_delivery_charge

    if request.method == "POST":
        delivery_type = request.form.get("delivery_type", "delivery").strip()
        pickup_time = request.form.get("pickup_time", "ASAP").strip()
        payment_method = request.form.get("payment_method", "cash").strip()
        name = request.form.get("name", user.name).strip()
        phone = request.form.get("phone", user.phone or "").strip()
        address = request.form.get("address", user.address or "").strip()
        city_area = request.form.get("city_area", user.city or "Kathmandu").strip()
        landmark = request.form.get("landmark", "").strip()
        delivery_notes = request.form.get("delivery_notes", "").strip()

        # Validation
        errors = []
        if not phone or len(phone) < 7:
            errors.append("A valid phone number is required for order contact.")
        if delivery_type == "delivery" and (not address or len(address) < 3):
            errors.append("Delivery address is required for food delivery.")

        valid_payments = ("cash", "esewa", "khalti", "qr")
        if payment_method not in valid_payments:
            errors.append(f"Invalid payment method selected. Choose from: {', '.join(valid_payments)}")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "student/checkout.html",
                user=user,
                items=items,
                subtotal=subtotal,
                delivery_charge=default_delivery_charge if delivery_type == "delivery" else 0.0,
                total=default_total if delivery_type == "delivery" else subtotal,
                free_delivery_threshold=Config.FREE_DELIVERY_THRESHOLD,
                default_delivery_fee=Config.DEFAULT_DELIVERY_CHARGE,
            )

        # Calculate final charges based on delivery type
        delivery_charge = manager.get_delivery_charge(delivery_type)
        total_amount = subtotal + delivery_charge

        # Save user address preference if provided
        if address and not user.address:
            user.address = address
        if phone and not user.phone:
            user.phone = phone
        if city_area and not user.city:
            user.city = city_area

        # Create Order
        order = Order(
            user_id=user.id,
            total_amount=total_amount,
            status="pending",
            payment_method=payment_method,
            payment_status="pending",
            pickup_time=pickup_time,
            delivery_type=delivery_type,
            delivery_address=address if delivery_type == "delivery" else "Store Counter Pickup",
            city_area=city_area if delivery_type == "delivery" else "",
            landmark=landmark if delivery_type == "delivery" else "",
            phone_number=phone,
            delivery_notes=delivery_notes,
            delivery_charge=delivery_charge,
        )
        db.session.add(order)
        db.session.flush()

        for entry in items:
            menu_item = entry["item"]
            qty = entry["quantity"]
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=qty,
                    price=menu_item.price,
                )
            )

        # Process payment branch
        if payment_method == "esewa":
            esewa_handler = EsewaPaymentHandler()
            success_url = url_for("student.esewa_success", _external=True)
            failure_url = url_for("student.esewa_failure", order_id=order.id, _external=True)
            esewa_data = esewa_handler.prepare_payment_request(
                order=order,
                success_url=success_url,
                failure_url=failure_url,
            )
            order.transaction_id = esewa_data["transaction_uuid"]
            db.session.commit()
            return render_template("student/esewa_redirect.html", order=order, esewa_data=esewa_data)

        elif payment_method == "cash":
            # Cash on Delivery / Cash on Pickup: deduct inventory and confirm order
            for entry in items:
                menu_item = entry["item"]
                qty = entry["quantity"]
                menu_item.stock -= qty
                if menu_item.stock <= 0:
                    menu_item.is_available = False
            order.transaction_id = f"COD-ORD-{order.id}"
            db.session.commit()
            save_cart({})
            flash(
                f"Order #{order.id} placed successfully! Please pay Rs. {total_amount:.0f} in cash upon food arrival.",
                "success",
            )
            return redirect(url_for("student.order_confirmation", order_id=order.id))

        else:
            # Khalti / QR simulated digital payment flow
            for entry in items:
                menu_item = entry["item"]
                qty = entry["quantity"]
                menu_item.stock -= qty
                if menu_item.stock <= 0:
                    menu_item.is_available = False
            order.payment_status = "completed"
            order.status = "confirmed"
            order.transaction_id = f"{payment_method.upper()}-TXN-{order.id}"
            db.session.commit()
            save_cart({})
            flash(f"Order #{order.id} confirmed with {payment_method.upper()} payment!", "success")
            return redirect(url_for("student.order_confirmation", order_id=order.id))

    return render_template(
        "student/checkout.html",
        user=user,
        items=items,
        subtotal=subtotal,
        delivery_charge=default_delivery_charge,
        total=default_total,
        free_delivery_threshold=Config.FREE_DELIVERY_THRESHOLD,
        default_delivery_fee=Config.DEFAULT_DELIVERY_CHARGE,
    )


@student_bp.route("/payment/esewa/success", methods=["GET"])
@login_required
@role_required("student")
def esewa_success():
    """
    eSewa payment success callback handler.
    Decodes response data, verifies signature and status, confirms order and deducts inventory.
    """
    from services.payment_processor import EsewaPaymentHandler

    encoded_data = request.args.get("data")
    if not encoded_data:
        flash("No response data received from eSewa payment gateway.", "danger")
        return redirect(url_for("student.cart"))

    esewa_handler = EsewaPaymentHandler()
    verification = esewa_handler.verify_response(encoded_data)

    if not verification.get("verified"):
        flash(
            f"eSewa payment verification failed: {verification.get('error', 'Unverified transaction')}. Please contact support.",
            "danger",
        )
        return redirect(url_for("student.cart"))

    transaction_uuid = verification.get("transaction_uuid", "")
    order = None

    if transaction_uuid:
        order = Order.query.filter_by(transaction_id=transaction_uuid).first()
        if not order and "-" in transaction_uuid:
            try:
                parts = transaction_uuid.split("-")
                if len(parts) >= 2 and parts[1].isdigit():
                    order = Order.query.get(int(parts[1]))
            except (ValueError, IndexError):
                pass

    if not order or order.user_id != session["user_id"]:
        flash("Order associated with the verified eSewa payment could not be located.", "danger")
        return redirect(url_for("student.cart"))

    # If order is not yet marked completed, deduct stock and update status
    if order.payment_status != "completed":
        for item in order.items:
            menu_item = item.menu_item
            if menu_item:
                menu_item.stock = max(0, menu_item.stock - item.quantity)
                if menu_item.stock <= 0:
                    menu_item.is_available = False

        order.payment_status = "completed"
        order.status = "confirmed"
        order.transaction_id = verification.get("transaction_code") or order.transaction_id
        db.session.commit()
        save_cart({})

    flash("eSewa payment verified successfully! Your food order is confirmed.", "success")
    return redirect(url_for("student.order_confirmation", order_id=order.id))


@student_bp.route("/payment/esewa/failure", methods=["GET"])
@login_required
@role_required("student")
def esewa_failure():
    """
    eSewa payment failure / cancellation callback handler.
    Preserves customer cart so they can retry or switch payment method.
    """
    order_id = request.args.get("order_id")
    if order_id:
        order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()
        if order and order.payment_status == "pending" and order.status == "pending":
            order.payment_status = "failed"
            order.status = "cancelled"
            db.session.commit()

    flash(
        "eSewa payment was cancelled or could not be completed. Your cart has been saved so you can try again or choose Cash on Delivery.",
        "warning",
    )
    return redirect(url_for("student.checkout"))



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
    from services.cart_manager import CartManager
    cart_data = get_cart()
    manager = CartManager(cart_data)
    items = []
    subtotal = 0.0
    for cart_item in manager.get_cart_items():
        subtotal += cart_item.line_total
        items.append(cart_item.to_dict())
    delivery_charge = manager.get_delivery_charge("delivery") if items else 0.0
    total = subtotal + delivery_charge
    return jsonify({
        "items": items,
        "subtotal": subtotal,
        "delivery_charge": delivery_charge,
        "total": total,
        "count": cart_count(),
    })



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
