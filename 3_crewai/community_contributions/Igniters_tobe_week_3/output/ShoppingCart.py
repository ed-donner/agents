from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from output.Pricing import calculate_total_price
from output.ProductCatalog import product_catalog


@dataclass
class CartItem:
    product_id: str
    quantity: int = 1
    added_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self, product):
        return {
            "product_id": self.product_id,
            "quantity": self.quantity,
            "added_at": self.added_at.isoformat(),
            "product": product.to_dict(),
            "item_total": round(product.price * self.quantity, 2),
        }


class ShoppingCart:
    def __init__(self, user_id=None, catalog=None):
        self.cart_id = str(uuid4())
        self.user_id = user_id
        self.catalog = catalog or product_catalog
        self.items = {}
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at

    def add_item(self, product_id, quantity=1):
        quantity = int(quantity)
        if quantity <= 0:
            return False, "Quantity must be greater than zero"
        product = self.catalog.get_product(product_id)
        if not product:
            return False, "Product not found"
        current_quantity = self.items.get(product_id).quantity if product_id in self.items else 0
        if current_quantity + quantity > product.stock:
            return False, "Insufficient stock"
        if product_id in self.items:
            self.items[product_id].quantity += quantity
        else:
            self.items[product_id] = CartItem(product_id=product_id, quantity=quantity)
        self.updated_at = datetime.now(UTC)
        return True, "Item added to cart"

    def remove_item(self, product_id):
        if product_id not in self.items:
            return False, "Item not in cart"
        del self.items[product_id]
        self.updated_at = datetime.now(UTC)
        return True, "Item removed from cart"

    def update_item_quantity(self, product_id, quantity):
        quantity = int(quantity)
        if product_id not in self.items:
            return False, "Item not in cart"
        if quantity <= 0:
            return self.remove_item(product_id)
        product = self.catalog.get_product(product_id)
        if not product:
            return False, "Product not found"
        if quantity > product.stock:
            return False, "Insufficient stock"
        self.items[product_id].quantity = quantity
        self.updated_at = datetime.now(UTC)
        return True, "Item quantity updated"

    def get_all_items(self):
        rows = []
        for product_id, item in self.items.items():
            product = self.catalog.get_product(product_id)
            if product:
                rows.append(item.to_dict(product))
        return rows

    def get_total(self, region=None):
        pricing_items = []
        for product_id, item in self.items.items():
            product = self.catalog.get_product(product_id)
            if product:
                pricing_items.append(
                    {
                        "price": product.price,
                        "quantity": item.quantity,
                        "category": product.category_id,
                    }
                )
        return calculate_total_price(pricing_items, region)

    def clear(self):
        self.items = {}
        self.updated_at = datetime.now(UTC)
        return True, "Cart cleared"


active_carts = {}


def get_cart(user_id):
    if user_id not in active_carts:
        active_carts[user_id] = ShoppingCart(user_id=user_id)
    return active_carts[user_id]


def add_item(user_id, product_id, quantity=1):
    return get_cart(user_id).add_item(product_id, quantity)


def remove_item(user_id, product_id):
    return get_cart(user_id).remove_item(product_id)


def update_item_quantity(user_id, product_id, quantity):
    return get_cart(user_id).update_item_quantity(product_id, quantity)


def get_cart_contents(user_id):
    return get_cart(user_id).get_all_items()


def get_cart_total(user_id, region=None):
    return get_cart(user_id).get_total(region)


def clear_cart(user_id):
    return get_cart(user_id).clear()
