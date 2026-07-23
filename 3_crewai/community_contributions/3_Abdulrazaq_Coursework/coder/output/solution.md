I wrote a Python program in the sandbox to compute the first 1,000,000 terms of the Leibniz series and multiply the sum by 4.

File created: `leibniz_pi.py`

Code:
```python
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
```

I ran it successfully, and the output was:
```text
3.1415916535897743
```