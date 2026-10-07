from datetime import datetime, timezone

from models import db


ORDER_STATUSES = ("pending", "confirmed", "preparing", "ready", "completed", "cancelled")
PAYMENT_METHODS = ("cash", "esewa", "khalti", "qr")
PAYMENT_STATUSES = ("pending", "completed", "failed")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.Enum(*ORDER_STATUSES, name="order_status"),
        default="pending",
        nullable=False,
    )
    payment_method = db.Column(db.Enum(*PAYMENT_METHODS, name="payment_method"), nullable=False)
    payment_status = db.Column(
        db.Enum(*PAYMENT_STATUSES, name="payment_status"),
        default="pending",
        nullable=False,
    )
    pickup_time = db.Column(db.String(50), nullable=True)  # Delivery slot or pickup time
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Online Food Delivery Fields
    delivery_type = db.Column(db.String(20), default="delivery", nullable=False)  # 'delivery' or 'pickup'
    delivery_address = db.Column(db.String(255), nullable=True)
    city_area = db.Column(db.String(100), nullable=True)
    landmark = db.Column(db.String(150), nullable=True)
    phone_number = db.Column(db.String(30), nullable=True)
    delivery_notes = db.Column(db.Text, nullable=True)
    delivery_charge = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="order", lazy=True)

    @property
    def is_delivery(self):
        return self.delivery_type != "pickup"

    @property
    def status_label(self):
        """Food-delivery-friendly status text."""
        if self.status == "pending":
            return "Order Placed"
        elif self.status == "confirmed":
            return "Payment Confirmed" if self.payment_status == "completed" else "Order Confirmed"
        elif self.status == "preparing":
            return "Preparing Food"
        elif self.status == "ready":
            return "Out for Delivery" if self.is_delivery else "Ready for Pickup"
        elif self.status == "completed":
            return "Delivered" if self.is_delivery else "Collected"
        elif self.status == "cancelled":
            return "Cancelled"
        return self.status.title()

    @property
    def full_delivery_address(self):
        if not self.is_delivery:
            return "Counter Pickup"
        parts = []
        if self.delivery_address:
            parts.append(self.delivery_address)
        if self.landmark:
            parts.append(f"Near {self.landmark}")
        if self.city_area:
            parts.append(self.city_area)
        return ", ".join(parts) if parts else "Address not provided"

    def to_dict(self, include_items=True, include_user=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "total_amount": float(self.total_amount),
            "status": self.status,
            "status_label": self.status_label,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "pickup_time": self.pickup_time,
            "delivery_type": self.delivery_type,
            "delivery_address": self.delivery_address,
            "city_area": self.city_area,
            "landmark": self.landmark,
            "phone_number": self.phone_number,
            "delivery_notes": self.delivery_notes,
            "delivery_charge": float(self.delivery_charge) if self.delivery_charge else 0.0,
            "transaction_id": self.transaction_id,
            "full_delivery_address": self.full_delivery_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_user and self.user:
            data["user"] = {
                "name": self.user.name,
                "email": self.user.email,
                "student_id": self.user.student_id,
                "phone": self.phone_number or self.user.phone,
            }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data



class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "menu_item_id": self.menu_item_id,
            "quantity": self.quantity,
            "price": float(self.price),
            "subtotal": float(self.price) * self.quantity,
            "menu_item": self.menu_item.to_dict(include_category=False) if self.menu_item else None,
        }
