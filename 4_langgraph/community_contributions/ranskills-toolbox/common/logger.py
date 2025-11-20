import os
import logging
from typing import Any

from dotenv import load_dotenv

load_dotenv(override=True)

os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def pretty_print(label: str, value: Any, width: int = 80, char: str = '=') -> None:
    """
    Pretty print a label and value with centered formatting.

    Args:
        label: The label/caption to display
        value: The value to display (will be converted to string)
        width: Total width of the display (default: 80)
        char: Character to use for decoration (default: "=")
    """
    value_str = str(value)

    # Create label line: "========== Label =========="
    label_with_spaces = f' {label} '
    label_padding = (width - len(label_with_spaces)) // 2
    label_line = (
        char * label_padding
        + label_with_spaces
        + char * (width - label_padding - len(label_with_spaces))
    )

    # Center the value
    value_padding = (width - len(value_str)) // 2
    value_line = ' ' * value_padding + value_str

    # Print everything
    print(label_line)
    print(value_line)
    print(char * width)
