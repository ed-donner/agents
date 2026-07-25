from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from output.ProductCatalog import product_catalog
from output.ShoppingCart import clear_cart, get_cart
from output.UserManagement import get_user_details


class OrderStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    user_id: str
    items: list
    shipping_address: dict
    payment_info: dict
    subtotal: float
    tax: float
    shipping_cost: float
    total: float
    order_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = OrderStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_status(self, new_status):
        self.status = new_status
        self.updated_at = datetime.now(UTC)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": self.items,
            "shipping_address": self.shipping_address,
            "payment_info": self.payment_info,
            "subtotal": self.subtotal,
            "tax": self.tax,
            "shipping_cost": self.shipping_cost,
            "total": self.total,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class OrderManager:
    def __init__(self):
        self.orders = {}
        self.user_orders = {}

    def create_order(self, user_id, shipping_address, payment_info, region=None):
        if not get_user_details(user_id):
            return False, "User not found"
        cart = get_cart(user_id)
        cart_items = cart.get_all_items()
        if not cart_items:
            return False, "Cart is empty"
        for item in cart_items:
            product = product_catalog.get_product(item["product_id"])
            if not product or item["quantity"] > product.stock:
                return False, "Insufficient stock for one or more items"
        totals = cart.get_total(region)
        shipping_cost = 0.0 if totals["subtotal"] >= 100 else 5.0
        order_items = []
        for item in cart_items:
            product = product_catalog.get_product(item["product_id"])
            product_catalog.adjust_stock(product.product_id, -item["quantity"])
            order_items.append(
                {
                    "product_id": product.product_id,
                    "name": product.name,
                    "price": product.price,
                    "quantity": item["quantity"],
                }
            )
        masked_payment = {
            "last_four": str(payment_info.get("card_number", ""))[-4:],
            "method": payment_info.get("method", "card"),
        }
        order = Order(
            user_id=user_id,
            items=order_items,
            shipping_address=shipping_address,
            payment_info=masked_payment,
            subtotal=totals["subtotal"],
            tax=totals["tax"],
            shipping_cost=shipping_cost,
            total=round(totals["total"] + shipping_cost, 2),
        )
        self.orders[order.order_id] = order
        self.user_orders.setdefault(user_id, []).append(order.order_id)
        clear_cart(user_id)
        return True, order.to_dict()

    def update_order_status(self, order_id, new_status):
        order = self.orders.get(order_id)
        if not order:
            return False, "Order not found"
        order.update_status(new_status)
        return True, order.to_dict()

    def get_order_status(self, order_id):
        order = self.orders.get(order_id)
        if not order:
            return None
        return {"order_id": order_id, "status": order.status}

    def get_order_history(self, user_id):
        return [self.orders[order_id].to_dict() for order_id in self.user_orders.get(user_id, [])]


order_manager = OrderManager()


def create_order(user_id, shipping_address, payment_info, region=None):
    return order_manager.create_order(user_id, shipping_address, payment_info, region)


def update_order_status(order_id, new_status):
    return order_manager.update_order_status(order_id, new_status)


def get_order_status(order_id):
    return order_manager.get_order_status(order_id)


def get_order_history(user_id):
    return order_manager.get_order_history(user_id)
