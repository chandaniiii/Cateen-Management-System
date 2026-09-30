"""
Campus Canteen Management System — Cart Manager Class (OOP: Encapsulation)
Encapsulates shopping cart state, items retrieval, quantity adjustments,
subtotal calculations, and stock validation.
"""

from typing import Any, Dict, List
from models.menu_item import MenuItem


class CartItem:
    """Represents an individual item inside the shopping cart."""

    def __init__(self, menu_item: MenuItem, quantity: int):
        self.menu_item = menu_item
        self.quantity = quantity

    @property
    def price(self) -> float:
        return float(self.menu_item.price)

    @property
    def line_total(self) -> float:
        return self.price * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "menu_item_id": self.menu_item.id,
            "name": self.menu_item.name,
            "price": self.price,
            "quantity": self.quantity,
            "line_total": self.line_total,
            "image": self.menu_item.image or "/static/images/food-placeholder.jpg",
            "stock": self.menu_item.stock,
            "is_available": self.menu_item.is_available,
        }


class CartManager:
    """
    Manages session-based shopping cart operations.
    Demonstrates OOP encapsulation of cart business logic.
    """

    def __init__(self, session_cart: Dict[str, int] = None):
        # Store internal dictionary of {str(item_id): int(quantity)}
        self._cart: Dict[str, int] = dict(session_cart) if session_cart else {}

    @property
    def raw_cart(self) -> Dict[str, int]:
        """Returns internal raw dictionary for storing in Flask session."""
        return self._cart

    @property
    def total_count(self) -> int:
        """Returns total quantity count of all items in cart."""
        return sum(self._cart.values())

    def is_empty(self) -> bool:
        """Checks if cart has no items."""
        return len(self._cart) == 0

    def add_item(self, menu_item_id: int, quantity: int = 1) -> None:
        """
        Adds a specified quantity of a food item to the cart.
        Validates item availability and stock bounds.
        """
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")

        item = MenuItem.query.get(menu_item_id)
        if not item:
            raise ValueError("Food item not found")

        if not item.is_available or item.stock <= 0:
            raise ValueError(f"'{item.name}' is currently out of stock")

        key = str(menu_item_id)
        current_qty = self._cart.get(key, 0)
        new_qty = current_qty + quantity

        if new_qty > item.stock:
            raise ValueError(f"Only {item.stock} unit(s) of '{item.name}' available in stock")

        self._cart[key] = new_qty

    def update_quantity(self, menu_item_id: int, quantity: int) -> None:
        """
        Updates the exact quantity of an item in the cart.
        If quantity <= 0, the item is removed.
        """
        key = str(menu_item_id)
        if quantity <= 0:
            self._cart.pop(key, None)
            return

        item = MenuItem.query.get(menu_item_id)
        if not item:
            raise ValueError("Food item not found")

        if quantity > item.stock:
            raise ValueError(f"Only {item.stock} unit(s) of '{item.name}' available in stock")

        self._cart[key] = quantity

    def remove_item(self, menu_item_id: int) -> None:
        """Removes an item completely from the cart."""
        key = str(menu_item_id)
        self._cart.pop(key, None)

    def clear(self) -> None:
        """Empties all items from the cart."""
        self._cart.clear()

    def get_cart_items(self) -> List[CartItem]:
        """
        Retrieves all valid CartItem objects loaded from database.
        Cleans up any deleted or invalid items automatically.
        """
        items: List[CartItem] = []
        invalid_keys = []

        for item_id_str, qty in list(self._cart.items()):
            try:
                item_id = int(item_id_str)
                menu_item = MenuItem.query.get(item_id)
                if menu_item:
                    items.append(CartItem(menu_item=menu_item, quantity=qty))
                else:
                    invalid_keys.append(item_id_str)
            except (ValueError, TypeError):
                invalid_keys.append(item_id_str)

        for key in invalid_keys:
            self._cart.pop(key, None)

        return items

    def get_subtotal(self) -> float:
        """Calculates and returns total price of items in cart."""
        return sum(item.line_total for item in self.get_cart_items())

    def validate_for_checkout(self) -> List[CartItem]:
        """
        Validates all cart items against live inventory for checkout.
        Raises ValueError if cart is empty or any item exceeds available stock.
        """
        cart_items = self.get_cart_items()
        if not cart_items:
            raise ValueError("Your cart is empty. Please add items before checkout.")

        for cart_item in cart_items:
            item = cart_item.menu_item
            if not item.is_available or item.stock < cart_item.quantity:
                raise ValueError(
                    f"'{item.name}' has only {item.stock} left in stock. Please adjust your cart quantity."
                )

        return cart_items
