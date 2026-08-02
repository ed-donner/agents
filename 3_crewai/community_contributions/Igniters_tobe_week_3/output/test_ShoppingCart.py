import unittest

from output.ProductCatalog import ProductCatalog
from output.ShoppingCart import ShoppingCart


class TestShoppingCart(unittest.TestCase):
    def setUp(self):
        self.catalog = ProductCatalog()
        self.product = self.catalog.list_products()[0]
        self.cart = ShoppingCart(user_id="user-1", catalog=self.catalog)

    def test_add_item(self):
        success, message = self.cart.add_item(self.product["product_id"], 2)
        self.assertTrue(success)
        self.assertEqual(message, "Item added to cart")
        self.assertEqual(len(self.cart.get_all_items()), 1)

    def test_update_and_remove_item(self):
        self.cart.add_item(self.product["product_id"], 1)
        success, message = self.cart.update_item_quantity(self.product["product_id"], 3)
        self.assertTrue(success)
        self.assertEqual(message, "Item quantity updated")
        success, message = self.cart.remove_item(self.product["product_id"])
        self.assertTrue(success)
        self.assertEqual(message, "Item removed from cart")
        self.assertEqual(self.cart.get_all_items(), [])

    def test_cart_total(self):
        self.cart.add_item(self.product["product_id"], 2)
        totals = self.cart.get_total()
        self.assertGreater(totals["subtotal"], 0)
        self.assertGreater(totals["total"], totals["subtotal"])


if __name__ == "__main__":
    unittest.main()
