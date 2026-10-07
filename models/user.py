from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from models import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    student_id = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    role = db.Column(db.Enum("student", "staff", "admin", name="user_roles"), default="student", nullable=False)
    status = db.Column(db.Enum("active", "inactive", name="user_status"), default="active", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    orders = db.relationship("Order", backref="user", lazy=True)
    reviews = db.relationship("Review", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "student_id": self.student_id,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "role": self.role,
            "display_role": "Customer" if self.role == "student" else self.role.title(),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

