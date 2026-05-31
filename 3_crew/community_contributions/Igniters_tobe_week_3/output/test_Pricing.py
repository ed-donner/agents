import unittest

from output.Pricing import PriceCalculator


class TestPricing(unittest.TestCase):
    def test_default_tax(self):
        calculator = PriceCalculator(default_tax_rate=0.1)
        self.assertEqual(calculator.calculate_tax(50), 5.0)

    def test_specific_tax_rate(self):
        calculator = PriceCalculator(default_tax_rate=0.1)
        calculator.set_tax_rate(category="books", rate=0.05)
        self.assertEqual(calculator.calculate_tax(100, category="books"), 5.0)

    def test_total_price(self):
        calculator = PriceCalculator(default_tax_rate=0.1)
        totals = calculator.calculate_total_price(
            [
                {"price": 10, "quantity": 2, "category": "a"},
                {"price": 5, "quantity": 1, "category": "b"},
            ]
        )
        self.assertEqual(totals["subtotal"], 25.0)
        self.assertEqual(totals["tax"], 2.5)
        self.assertEqual(totals["total"], 27.5)


if __name__ == "__main__":
    unittest.main()
