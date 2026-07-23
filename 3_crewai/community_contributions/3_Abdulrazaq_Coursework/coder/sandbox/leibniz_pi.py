def leibniz_pi(n_terms: int = 1_000_000) -> float:
    total = 0.0
    sign = 1.0
    for i in range(n_terms):
        total += sign / (2 * i + 1)
        sign = -sign
    return 4 * total


if __name__ == "__main__":
    result = leibniz_pi(1_000_000)
    print(result)
