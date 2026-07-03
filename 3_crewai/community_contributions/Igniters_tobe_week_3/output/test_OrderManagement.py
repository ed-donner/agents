import unittest
from uuid import uuid4

from output.OrderManagement import create_order, get_order_history
from output.ProductCatalog import product_catalog
from output.ShoppingCart import add_item, clear_cart
from output.UserManagement import register_user


class TestOrderManagement(unittest.TestCase):
    def setUp(self):
        self.username = f"user_{uuid4().hex[:8]}"
        success, self.user_id = register_user(self.username, f"{self.username}@example.com", "secret")
        self.assertTrue(success)
        self.product = product_catalog.list_products()[0]
        product_catalog.set_stock(self.product["product_id"], 10)
        clear_cart(self.user_id)

    def test_create_order_moves_cart_to_history(self):
        add_item(self.user_id, self.product["product_id"], 2)
        starting_stock = product_catalog.get_product(self.product["product_id"]).stock
        success, order = create_order(
            self.user_id,
            {"line1": "1 Main", "city": "Lagos", "state": "LA", "postal_code": "100001"},
            {"method": "card", "card_number": "4111111111111111"},
        )
        self.assertTrue(success)
        self.assertEqual(order["status"], "PENDING")
        self.assertEqual(len(get_order_history(self.user_id)), 1)
        ending_stock = product_catalog.get_product(self.product["product_id"]).stock
        self.assertEqual(ending_stock, starting_stock - 2)


if __name__ == "__main__":
    unittest.main()
