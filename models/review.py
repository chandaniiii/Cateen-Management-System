from datetime import datetime, timezone

from models import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "menu_item_id": self.menu_item_id,
            "order_id": self.order_id,
            "rating": self.rating,
            "comment": self.comment,
            "is_visible": self.is_visible,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_name": self.user.name if self.user else "Anonymous",
            "menu_item_name": self.menu_item.name if self.menu_item else "",
        }
