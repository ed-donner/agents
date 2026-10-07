from decimal import Decimal, getcontext


def calculate_pi_leibniz(terms: int) -> Decimal:
    getcontext().prec = 50
    total = Decimal(0)
    sign = 1
    for n in range(terms):
        denominator = 2 * n + 1
        term = Decimal(1) / Decimal(denominator)
        total += term if sign > 0 else -term
        sign *= -1
    return total * 4


if __name__ == "__main__":
    terms = 1_000_000
    result = calculate_pi_leibniz(terms)
    print(f"Pi approximation using {terms} terms: {result}")
