from agents import function_tool
from utils.globals import span


def _multiply_numbers_impl(a: float, b: float) -> float:
    """
    Multiplies two numbers and returns the result.

    Args:
        a: The first number.
        b: The second number.
    """
    with span("multiply_numbers", "Multiplying two numbers"):
        print(f"-> Tool called: multiply_numbers({a}, {b})")
        result = a * b
        print(f"-> Tool result: {result}")
        return result


# Create the tool for use with agents
multiply_numbers = function_tool(_multiply_numbers_impl)

