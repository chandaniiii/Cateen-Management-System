import os
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template
from werkzeug.security import generate_password_hash

from config import Config
from models import db
from models.category import Category
from models.menu_item import MenuItem
from models.order import Order, OrderItem
from models.review import Review
from models.user import User
from routes.admin import admin_bp
from routes.api import api_bp
from routes.auth import auth_bp
from routes.main import main_bp
from routes.staff import staff_bp
from routes.student import student_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.context_processor
    def inject_globals():
        from flask import session

        return {
            "current_year": datetime.now(timezone.utc).year,
            "session_user": {
                "id": session.get("user_id"),
                "name": session.get("name"),
                "role": session.get("role"),
                "email": session.get("email"),
            }
            if session.get("user_id")
            else None,
        }

    with app.app_context():
        db.create_all()
        seed_database()

    return app


def seed_database():
    """Seed comprehensive initial data if database is empty."""
    if User.query.first():
        return

    print("Seeding database with initial users, categories, menu items, sample orders, and reviews...")
    default_password = "Password123!"
    password_hash = generate_password_hash(default_password)

    # 1. Initial Users
    admin = User(
        name="Admin User",
        email="admin@canteen.com",
        password_hash=password_hash,
        role="admin",
        status="active",
        phone="9801111111",
    )
    staff = User(
        name="Canteen Staff",
        email="staff@canteen.com",
        password_hash=password_hash,
        role="staff",
        status="active",
        phone="9802222222",
    )
    student = User(
        name="Aayush Sharma",
        email="student@college.com",
        password_hash=password_hash,
        student_id="STU2024001",
        phone="9841234567",
        role="student",
        status="active",
    )
    student2 = User(
        name="Pooja Thapa",
        email="pooja@college.com",
        password_hash=password_hash,
        student_id="STU2024045",
        phone="9812345678",
        role="student",
        status="active",
    )
    student3 = User(
        name="Bikash KC",
        email="bikash@college.com",
        password_hash=password_hash,
        student_id="STU2024089",
        phone="9860123456",
        role="student",
        status="active",
    )
    db.session.add_all([admin, staff, student, student2, student3])
    db.session.flush()

    # 2. Categories
    categories_data = [
        ("Breakfast", "Fresh morning meals, bakery, and light breakfast items"),
        ("Snacks", "Quick crispy bites, fries, and afternoon appetizers"),
        ("Main Course", "Hearty traditional and filling meals for lunch and dinner"),
        ("Fast Food", "Burgers, pizzas, sandwiches, and student favorites"),
        ("Drinks", "Hot teas, brewed coffee, cold beverages, and fresh lassi"),
        ("Desserts", "Sweet treats and dessert delights to finish your meal"),
    ]
    categories = {}
    for name, desc in categories_data:
        cat = Category(name=name, description=desc)
        db.session.add(cat)
        categories[name] = cat
    db.session.flush()

    # 3. Menu Items with realistic Nepalese pricing in NPR & dedicated SVGs
    menu_data = [
        ("Steam Momo (Buff/Veg)", "Main Course", "Authentic freshly steamed dumplings served with hot spicy sesame tomato chutney", 120, 50, 10, "/static/images/momo.svg"),
        ("Veg / Chicken Chowmein", "Main Course", "Wok-tossed noodles with shredded vegetables and special canteen spice blend", 100, 45, 10, "/static/images/chowmein.svg"),
        ("Egg Fried Rice", "Main Course", "Aromatic stir-fried rice loaded with scrambled egg, garden peas, and spring onions", 110, 35, 10, "/static/images/fried-rice.svg"),
        ("Special Nepali Dal Bhat Set", "Main Course", "Complete traditional thali with steamed rice, yellow lentils, seasonal tarkari, and pickle", 130, 30, 8, "/static/images/dal-bhat.svg"),
        ("Crispy Samosa (2 pcs)", "Snacks", "Golden crisp pastry triangles filled with spiced cumin potatoes and green peas", 30, 80, 15, "/static/images/samosa.svg"),
        ("Grilled Veg Sandwich", "Fast Food", "Toasted triple-layer sandwich with cheese, crisp cucumber, tomato, and mint chutney", 80, 40, 10, "/static/images/sandwich.svg"),
        ("Crispy Chicken Burger", "Fast Food", "Juicy chicken patty layered with lettuce, cheese slice, and creamy mayo sauce", 150, 30, 8, "/static/images/burger.svg"),
        ("Cheese Pizza Slice", "Fast Food", "Oven-baked crust topped with rich herb tomato sauce and melted mozzarella cheese", 180, 25, 8, "/static/images/pizza.svg"),
        ("Golden French Fries", "Snacks", "Crispy fried potato batons lightly salted and served with tomato ketchup", 90, 60, 12, "/static/images/fries.svg"),
        ("Aloo Paratha with Curd", "Breakfast", "Warm whole wheat stuffed flatbread served with fresh curd and spicy mixed pickle", 70, 40, 10, "/static/images/paratha.svg"),
        ("Masala Omelette & Toast", "Breakfast", "Fluffy 2-egg omelette with onions, green chillies, coriander, and toasted butter bread", 90, 35, 8, "/static/images/omelette.svg"),
        ("Hot Brewed Coffee", "Drinks", "Rich freshly brewed aromatic milk coffee to power through study sessions", 80, 100, 20, "/static/images/coffee.svg"),
        ("Nepali Masala Chiya", "Drinks", "Classic spiced milk tea infused with cardamom, ginger, and cloves", 40, 120, 25, "/static/images/chiya.svg"),
        ("Cold Drinks (300ml)", "Drinks", "Chilled soda bottle (Coke, Fanta, Sprite)", 60, 80, 15, "/static/images/cold-drinks.svg"),
        ("Sweet Curd Lassi", "Drinks", "Chilled creamy yogurt smoothie topped with sliced almonds", 70, 50, 10, "/static/images/lassi.svg"),
        ("Hot Gulab Jamun (2 pcs)", "Desserts", "Soft golden milk dough balls soaked in warm saffron cardamom sugar syrup", 50, 40, 10, "/static/images/gulab-jamun.svg"),
        ("Vanilla / Chocolate Ice Cream", "Desserts", "Creamy scoop of vanilla or rich chocolate ice cream", 60, 45, 10, "/static/images/ice-cream.svg"),
        ("Spicy Wai Wai Sadeko", "Snacks", "Crunchy instant noodles tossed with chopped onions, tomatoes, lime, and chilli powder", 50, 70, 15, "/static/images/wai-wai.svg"),
    ]

    items_map = {}
    for name, cat_name, desc, price, stock, min_stock, img in menu_data:
        item = MenuItem(
            name=name,
            category_id=categories[cat_name].id,
            description=desc,
            price=price,
            stock=stock,
            minimum_stock=min_stock,
            is_available=stock > 0,
            image=img,
        )
        db.session.add(item)
        items_map[name] = item

    db.session.flush()

    # 4. Sample Orders
    now = datetime.now(timezone.utc)
    order1 = Order(
        user_id=student.id,
        total_amount=200.00,
        status="completed",
        payment_method="esewa",
        payment_status="completed",
        pickup_time="ASAP",
        created_at=now - timedelta(days=3),
    )
    order2 = Order(
        user_id=student.id,
        total_amount=150.00,
        status="completed",
        payment_method="khalti",
        payment_status="completed",
        pickup_time="1:00 PM",
        created_at=now - timedelta(days=2),
    )
    order3 = Order(
        user_id=student2.id,
        total_amount=300.00,
        status="completed",
        payment_method="qr",
        payment_status="completed",
        pickup_time="12:00 PM",
        created_at=now - timedelta(days=1),
    )
    order4 = Order(
        user_id=student.id,
        total_amount=160.00,
        status="ready",
        payment_method="cash",
        payment_status="pending",
        pickup_time="ASAP",
        created_at=now - timedelta(minutes=25),
    )
    order5 = Order(
        user_id=student3.id,
        total_amount=220.00,
        status="preparing",
        payment_method="esewa",
        payment_status="completed",
        pickup_time="12:30 PM",
        created_at=now - timedelta(minutes=15),
    )
    order6 = Order(
        user_id=student2.id,
        total_amount=120.00,
        status="confirmed",
        payment_method="qr",
        payment_status="completed",
        pickup_time="1:00 PM",
        created_at=now - timedelta(minutes=5),
    )
    db.session.add_all([order1, order2, order3, order4, order5, order6])
    db.session.flush()

    # Order Items
    momo = items_map["Steam Momo (Buff/Veg)"]
    coffee = items_map["Hot Brewed Coffee"]
    burger = items_map["Crispy Chicken Burger"]
    pizza = items_map["Cheese Pizza Slice"]
    chiya = items_map["Nepali Masala Chiya"]
    lassi = items_map["Sweet Curd Lassi"]

    order_items = [
        OrderItem(order_id=order1.id, menu_item_id=momo.id, quantity=1, price=momo.price),
        OrderItem(order_id=order1.id, menu_item_id=coffee.id, quantity=1, price=coffee.price),
        OrderItem(order_id=order2.id, menu_item_id=burger.id, quantity=1, price=burger.price),
        OrderItem(order_id=order3.id, menu_item_id=momo.id, quantity=1, price=momo.price),
        OrderItem(order_id=order3.id, menu_item_id=pizza.id, quantity=1, price=pizza.price),
        OrderItem(order_id=order4.id, menu_item_id=momo.id, quantity=1, price=momo.price),
        OrderItem(order_id=order4.id, menu_item_id=chiya.id, quantity=1, price=chiya.price),
        OrderItem(order_id=order5.id, menu_item_id=burger.id, quantity=1, price=burger.price),
        OrderItem(order_id=order5.id, menu_item_id=lassi.id, quantity=1, price=lassi.price),
        OrderItem(order_id=order6.id, menu_item_id=momo.id, quantity=1, price=momo.price),
    ]
    db.session.add_all(order_items)

    # Sample Reviews
    rev1 = Review(
        user_id=student.id,
        menu_item_id=momo.id,
        order_id=order1.id,
        rating=5,
        comment="Best momo on campus! Steaming hot and the achar has the perfect punch.",
        is_visible=True,
        created_at=now - timedelta(days=3),
    )
    rev2 = Review(
        user_id=student.id,
        menu_item_id=coffee.id,
        order_id=order1.id,
        rating=4,
        comment="Great coffee to keep me awake during morning lectures.",
        is_visible=True,
        created_at=now - timedelta(days=3),
    )
    rev3 = Review(
        user_id=student2.id,
        menu_item_id=pizza.id,
        order_id=order3.id,
        rating=5,
        comment="Super cheesy with a crisp crust. Great value for money!",
        is_visible=True,
        created_at=now - timedelta(days=1),
    )
    rev4 = Review(
        user_id=student3.id,
        menu_item_id=burger.id,
        order_id=order2.id,
        rating=5,
        comment="The chicken burger was delicious, fresh buns and crispy patty.",
        is_visible=True,
        created_at=now - timedelta(days=2),
    )
    db.session.add_all([rev1, rev2, rev3, rev4])

    db.session.commit()
    print("Database successfully seeded with initial data!")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
