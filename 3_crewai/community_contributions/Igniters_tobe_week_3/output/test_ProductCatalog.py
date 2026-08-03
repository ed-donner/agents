import unittest

from output.ProductCatalog import ProductCatalog


class TestProductCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog = ProductCatalog()
        self.category_id = self.catalog.get_all_categories()[0]["category_id"]

    def test_seeded_products_exist(self):
        self.assertGreater(len(self.catalog.list_products()), 0)

    def test_add_and_search_product(self):
        success, product_id = self.catalog.add_product("Travel Mug", "Insulated mug", 18.5, self.category_id, stock=8)
        self.assertTrue(success)
        results = self.catalog.search_products("mug")
        self.assertTrue(any(product["product_id"] == product_id for product in results))

    def test_filter_by_category(self):
        products = self.catalog.get_products_by_category(self.category_id)
        self.assertTrue(all(product["category_id"] == self.category_id for product in products))


if __name__ == "__main__":
    unittest.main()
