from pydantic import BaseModel

class Order(BaseModel):
    customer_id: str
    item: str
    total_price: float
    status: str


def group_orders_by_customer_id(orders: list[Order]) -> dict:
    """Group orders by customer_id, returning a dictionary with customer_id as keys and lists of orders as values."""

    customer_ids = {order.customer_id for order in orders}
    grouped = dict.fromkeys(customer_ids, [])
    for order in orders:
        grouped[order.customer_id].append(order)
    return grouped