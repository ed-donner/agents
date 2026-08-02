import re
import time

from .config import reports_dir


def generate_safe_filename(topic: str, max_length: int = 100) -> str:
    filename = topic.lower()

    filename = re.sub(r'[\s]+', '_', filename)
    filename = re.sub(r'[^a-z0-9_-]', '', filename)

    timestamp = int(time.time())

    if len(filename) > max_length:
        filename = filename[:max_length].strip('_')

    filename = f'{filename}_{timestamp}'

    return filename


def write_file(file_path: str, content: str) -> None:
    with open(file_path, 'w') as f:
        f.write(content)


def write_report(filename: str, content: str) -> None:
    write_file(reports_dir / filename, content)
