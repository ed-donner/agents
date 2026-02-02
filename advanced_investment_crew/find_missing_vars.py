"""
Find all template variables in YAML files
"""

import re
from pathlib import Path

def find_all_variables(file_path):
    """Find all {variable} patterns"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
    matches = re.findall(pattern, content)
    
    return sorted(set(matches))

config_dir = Path('src/advanced_investment_crew/config')

all_vars = set()

print("=" * 80)
print("🔍 ALL TEMPLATE VARIABLES IN YAML FILES")
print("=" * 80)

for yaml_file in ['agents.yaml', 'tasks.yaml']:
    file_path = config_dir / yaml_file
    if file_path.exists():
        vars_found = find_all_variables(file_path)
        print(f"\n📄 {yaml_file}:")
        for var in vars_found:
            print(f"   - {var}")
            all_vars.add(var)

print("\n" + "=" * 80)
print("📋 COMPLETE LIST OF ALL VARIABLES:")
print("=" * 80)
for var in sorted(all_vars):
    print(f"   '{var}': 'TODO',")

print("\n" + "=" * 80)
print("✅ Copy these to your inputs dictionary in main.py")
print("=" * 80)
