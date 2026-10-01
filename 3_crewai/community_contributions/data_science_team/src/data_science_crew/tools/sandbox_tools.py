import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import subprocess

from crewai.tools import tool

# Set sandbox directory relative to project root
SANDBOX_DIR = Path(__file__).parents[3] / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


def generate_sample_data(filepath: Path) -> None:
    """Generate a realistic synthetic E-Commerce Sales dataset (data.csv)."""
    random.seed(42)
    categories = {
        "Electronics": [
            ("Wireless Ergonomic Mouse", 29.99),
            ("Mechanical RGB Keyboard", 89.99),
            ("UltraWide 34-inch Monitor", 449.99),
            ("USB-C Multi-port Docking Station", 59.99),
            ("Noise-Canceling Headphones", 199.99)
        ],
        "Furniture": [
            ("Ergonomic Mesh Office Chair", 249.99),
            ("Electric Height Adjustable Desk", 399.99),
            ("LED Monitor Desk Lamp", 34.99),
            ("Under-desk Cable Tray", 19.99)
        ],
        "Office Supplies": [
            ("Premium Leather Notebook", 14.99),
            ("Gel Ink Pens 12-pack", 9.99),
            ("Heavy Duty Desktop Stapler", 12.49),
            ("Dry Erase Whiteboard 36x24", 49.99)
        ],
        "Apparel": [
            ("Tech Fleece Hoodie", 54.99),
            ("Breathable Running Shoes", 79.99),
            ("Waterproof Backpack 25L", 64.99)
        ]
    }

    regions = ["North", "South", "East", "West"]
    customer_segments = ["Consumer", "Corporate", "Small Business"]
    payment_methods = ["Credit Card", "PayPal", "Bank Transfer", "Crypto"]

    start_date = datetime(2024, 1, 1)
    fieldnames = [
        "order_id", "order_date", "customer_segment", "region",
        "category", "product_name", "quantity", "unit_price",
        "discount_pct", "shipping_cost", "payment_method"
    ]

    rows = []
    for i in range(1, 201):
        cat = random.choice(list(categories.keys()))
        prod_name, base_price = random.choice(categories[cat])
        order_date = start_date + timedelta(days=random.randint(0, 365))
        quantity = random.choices([1, 2, 3, 4, 5, 8, 10], weights=[40, 25, 15, 10, 5, 3, 2])[0]
        discount = random.choice([0.0, 0.05, 0.10, 0.15, 0.20])
        shipping = round(random.uniform(4.99, 29.99), 2)

        rows.append({
            "order_id": f"ORD-{1000 + i}",
            "order_date": order_date.strftime("%Y-%m-%d"),
            "customer_segment": random.choice(customer_segments),
            "region": random.choice(regions),
            "category": cat,
            "product_name": prod_name,
            "quantity": quantity,
            "unit_price": base_price,
            "discount_pct": discount,
            "shipping_cost": shipping,
            "payment_method": random.choice(payment_methods)
        })

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def reset_sandbox() -> None:
    """Wipe the sandbox and re-initialize it as a clean sandbox folder with pyproject.toml and data.csv."""
    if not SANDBOX_DIR.exists():
        SANDBOX_DIR.mkdir(parents=True)
    else:
        for item in SANDBOX_DIR.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
            except Exception:
                pass

    pyproject_content = """[project]
name = "sandbox"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "gradio>=6.0.0",
    "pandas",
    "plotly",
    "numpy",
]

[tool.uv]
package = false
"""
    (SANDBOX_DIR / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # Seed sample dataset data.csv
    sample_csv = SANDBOX_DIR / "data.csv"
    generate_sample_data(sample_csv)


@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """
    List the filenames currently in the sandbox directory.

    Returns:
        A newline-separated list of filenames, or a message if the sandbox is empty.
    """
    names = sorted(p.name for p in SANDBOX_DIR.iterdir())
    return "\n".join(names) if names else "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """
    Read and return the text contents of a file in the sandbox directory.

    Args:
        filename: The name of the file to read (e.g. "data.csv").
    Returns:
        The file's contents, or a message if the file does not exist.
    """
    path = SANDBOX_DIR / filename
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return path.read_text(encoding="utf-8")


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """
    Write text to a file in the sandbox directory, replacing any existing file with the same name.

    Args:
        filename: The name of the file to write (e.g. "data_pipeline.py").
        content: The text content to write.
    Returns:
        A confirmation message.
    """
    path = SANDBOX_DIR / filename
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """
    Execute a Python file from the sandbox directory inside an ephemeral Docker container,
    with the sandbox mounted as the working directory, using `uv run` to run the code.

    Args:
        filename: The name of the Python file to run (e.g. "data_pipeline.py").
    Returns:
        The text printed to stdout by the executed script.
    """
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-e", "UV_PROJECT_ENVIRONMENT=/tmp/venv",
            "-v", f"{SANDBOX_DIR}:/workspace",
            "-w", "/workspace",
            "ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
            "uv", "run", filename,
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result.stdout if result.stdout else result.stderr


sandbox_tools = [list_sandbox_files, read_sandbox_file, write_sandbox_file, run_sandbox_python]


def _never_cache(*_args, **_kwargs) -> bool:
    return False


# Sandbox state changes between calls (files appear/change/run), so caching tool
# results would feed agents stale data. Opt out of CrewAI's default tool caching.
for _t in sandbox_tools:
    _t.cache_function = _never_cache
