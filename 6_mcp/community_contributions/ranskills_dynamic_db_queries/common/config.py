from pathlib import Path


base_dir = Path(__file__).parent.parent


data_dir = base_dir / 'data'
data_dir.mkdir(parents=True, exist_ok=True)
