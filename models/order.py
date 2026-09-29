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
    pickup_time = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="order", lazy=True)

    def to_dict(self, include_items=True, include_user=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "total_amount": float(self.total_amount),
            "status": self.status,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "pickup_time": self.pickup_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_user and self.user:
            data["user"] = {
                "name": self.user.name,
                "email": self.user.email,
                "student_id": self.user.student_id,
                "phone": self.user.phone,
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
