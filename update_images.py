from app import app
from models import db
from models.menu_item import MenuItem

image_map = {
    "Steam Momo (Buff/Veg)": "/static/images/momo.jpg",
    "Veg / Chicken Chowmein": "/static/images/chowmein.jpg",
    "Egg Fried Rice": "/static/images/fried-rice.jpg",
    "Special Nepali Dal Bhat Set": "/static/images/dal-bhat.jpg",
    "Crispy Samosa (2 pcs)": "/static/images/samosa.jpg",
    "Grilled Veg Sandwich": "/static/images/sandwich.jpg",
    "Crispy Chicken Burger": "/static/images/burger.jpg",
    "Cheese Pizza Slice": "/static/images/pizza.jpg",
    "Golden French Fries": "/static/images/fries.jpg",
    "Aloo Paratha with Curd": "/static/images/paratha.jpg",
    "Masala Omelette & Toast": "/static/images/omelette.jpg",
    "Hot Brewed Coffee": "/static/images/coffee.jpg",
    "Nepali Masala Chiya": "/static/images/chiya.jpg",
    "Cold Drinks (300ml)": "/static/images/cold-drinks.jpg",
    "Sweet Curd Lassi": "/static/images/lassi.jpg",
    "Hot Gulab Jamun (2 pcs)": "/static/images/gulab-jamun.jpg",
    "Vanilla / Chocolate Ice Cream": "/static/images/ice-cream.jpg",
    "Spicy Wai Wai Sadeko": "/static/images/wai-wai.jpg",
}

with app.app_context():
    for name, image_path in image_map.items():
        item = MenuItem.query.filter_by(name=name).first()
        if item:
            item.image = image_path
            print(f"Updated: {name}")

    db.session.commit()

print("New JPG version restored!")