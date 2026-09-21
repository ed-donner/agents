from pathlib import Path
import shutil

def purge_directory(path: str):
    """
    Removes the directory at 'path' (if it exists) and recreates it as empty.
    """
    p = Path(path)
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
