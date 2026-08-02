def calculate_pi_terms(n_terms: int = 1_000_000) -> float:
    total = 0.0
    sign = 1.0
    for i in range(n_terms):
        denom = 2 * i + 1
        total += sign / denom
        sign = -sign
    return 4 * total


if __name__ == "__main__":
    result = calculate_pi_terms()
    print(result)
