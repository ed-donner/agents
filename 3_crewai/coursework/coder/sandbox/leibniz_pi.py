def approximate_pi(terms=1_000_000):
    total = 0.0
    sign = 1.0
    for i in range(terms):
        total += sign / (2 * i + 1)
        sign = -sign
    return total * 4


if __name__ == "__main__":
    result = approximate_pi()
    print(result)
