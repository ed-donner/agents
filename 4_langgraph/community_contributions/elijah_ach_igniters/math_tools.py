from langchain_core.tools import tool, Tool


@tool
def add(x: int, y: int) -> int:
    """
    Takes two args numbers(x, y), and returns the result of the addition(x+y)
    Args:
        x: An integer
        y: An integer
    """
    return x + y



@tool
def sub(x: int, y: int) -> int:
    """
    Takes two numbers(x, y), and returns the result of the subtraction(x-y)
    Args:
        x: An integer
        y: An integer
    """
    return x - y



@tool
def div(x: int, y: int) -> int:
    """
    Takes two numbers(x, y), and returns the result of the division(x/y)
    Args:
        x: An integer
        y: An integer
    """
    return x / y



@tool
def mul(x: int, y: int) -> int:
    """
    Takes two numbers(x, y), and returns the result of the multiplication(x*y)
    Args:
        x: An integer
        y: An integer
    """
    return x * y



