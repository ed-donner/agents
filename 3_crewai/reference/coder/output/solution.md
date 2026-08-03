I wrote a Python program in the sandbox to calculate the first 1,000,000 terms of the alternating series

1 - 1/3 + 1/5 - 1/7 + ...

and multiply the total by 4.

Program saved as `solution.py`:

```python
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
```

I ran it in the sandbox, and the output was:

```text
3.1415916535897743
```

This is the computed approximation of π from the first 1,000,000 terms.