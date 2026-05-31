"""Reset buggy_kata back to its initial buggy state."""

from pathlib import Path
import shutil


def reset_buggy_kata_state() -> Path:
    """Restore src/utils.py from src/utils_buggy_original.py."""
    repo_root = Path(__file__).resolve().parent
    src = repo_root / "src" / "utils_buggy_original.py"
    dst = repo_root / "src" / "utils.py"

    if not src.exists():
        raise FileNotFoundError(f"Missing reset source file: {src}")

    shutil.copy(src, dst)
    return dst


if __name__ == "__main__":
    restored_file = reset_buggy_kata_state()
    print(f"Reset complete: {restored_file}")
