from datetime import datetime, timezone

from models import db


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    stock = db.Column(db.Integer, default=0, nullable=False)
    minimum_stock = db.Column(db.Integer, default=5, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    order_items = db.relationship("OrderItem", backref="menu_item", lazy=True)
    reviews = db.relationship("Review", backref="menu_item", lazy=True)

    @property
    def stock_status(self):
        if self.stock <= 0 or not self.is_available:
            return "out_of_stock"
        if self.stock <= self.minimum_stock:
            return "low_stock"
        return "in_stock"

    def to_dict(self, include_category=True):
        data = {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "image": self.image or "/static/images/food-placeholder.jpg",
            "stock": self.stock,
            "minimum_stock": self.minimum_stock,
            "is_available": self.is_available and self.stock > 0,
            "stock_status": self.stock_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_category and self.category:
            data["category"] = self.category.name
        return data
