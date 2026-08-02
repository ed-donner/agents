class PriceCalculator:
    def __init__(self, default_tax_rate=0.1):
        self.default_tax_rate = float(default_tax_rate)
        self.tax_rates = {}

    def set_tax_rate(self, category=None, region=None, rate=None):
        if rate is None:
            raise ValueError("Tax rate must be provided")
        self.tax_rates[(category, region)] = float(rate)

    def get_tax_rate(self, category=None, region=None):
        for key in (
            (category, region),
            (category, None),
            (None, region),
            (None, None),
        ):
            if key in self.tax_rates:
                return self.tax_rates[key]
        return self.default_tax_rate

    def calculate_tax(self, amount, category=None, region=None):
        return round(float(amount) * self.get_tax_rate(category, region), 2)

    def calculate_total_price(self, items, region=None):
        subtotal = 0.0
        tax = 0.0
        for item in items:
            line_total = float(item.get("price", 0)) * int(item.get("quantity", 1))
            subtotal += line_total
            tax += self.calculate_tax(line_total, item.get("category"), region)
        subtotal = round(subtotal, 2)
        tax = round(tax, 2)
        return {
            "subtotal": subtotal,
            "tax": tax,
            "total": round(subtotal + tax, 2),
        }


price_calculator = PriceCalculator()


def calculate_tax(amount, category=None, region=None):
    return price_calculator.calculate_tax(amount, category, region)


def calculate_total_price(items, region=None):
    return price_calculator.calculate_total_price(items, region)
