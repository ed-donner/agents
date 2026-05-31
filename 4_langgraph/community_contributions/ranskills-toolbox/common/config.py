from pathlib import Path


output_dir = Path('./.output')
output_dir.mkdir(parents=True, exist_ok=True)

reports_dir = output_dir / 'reports'
reports_dir.mkdir(parents=True, exist_ok=True)
