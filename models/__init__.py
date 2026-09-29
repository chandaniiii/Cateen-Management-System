from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User  # noqa: E402, F401
from models.category import Category  # noqa: E402, F401
from models.menu_item import MenuItem  # noqa: E402, F401
from models.order import Order, OrderItem  # noqa: E402, F401
from models.review import Review  # noqa: E402, F401
