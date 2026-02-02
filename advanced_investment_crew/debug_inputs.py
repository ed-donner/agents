"""
Debug: Print exactly what inputs are being sent
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

from advanced_investment_crew.crew import AdvancedInvestmentCrew

end_date = datetime.now()
start_date = end_date - timedelta(days=180)

inputs = {
    'market_type': 'US',
    'period': '6mo',
    'start_date': start_date.strftime('%Y-%m-%d'),
    'end_date': end_date.strftime('%Y-%m-%d'),
    'report_date': end_date.strftime('%Y-%m-%d'),
    'risk_free_rate': 4.5,
}

print("=" * 80)
print("📋 INPUTS DICTIONARY")
print("=" * 80)
for key, value in inputs.items():
    print(f"  '{key}': {value!r}")

print("\n" + "=" * 80)
print("🔍 CHECKING YAML FILES")
print("=" * 80)

# Check if start_date is actually used in YAML
import re

for yaml_file in ['agents.yaml', 'tasks.yaml']:
    yaml_path = Path(f'src/advanced_investment_crew/config/{yaml_file}')
    if yaml_path.exists():
        with open(yaml_path, 'r') as f:
            content = f.read()
        
        # Find all {start_date} occurrences
        matches = list(re.finditer(r'\{start_date\}', content))
        
        if matches:
            print(f"\n📄 {yaml_file}: Found {len(matches)} occurrences of {{start_date}}")
            for i, match in enumerate(matches[:3], 1):  # Show first 3
                line_num = content[:match.start()].count('\n') + 1
                # Get context
                lines = content.split('\n')
                context_start = max(0, line_num - 2)
                context_end = min(len(lines), line_num + 2)
                
                print(f"\n  Match {i} at line {line_num}:")
                for j in range(context_start, context_end):
                    prefix = ">>>" if j == line_num - 1 else "   "
                    print(f"  {prefix} {j+1:4d}: {lines[j]}")

print("\n" + "=" * 80)
print("🚀 ATTEMPTING TO CREATE CREW")
print("=" * 80)

try:
    crew = AdvancedInvestmentCrew()
    print("✅ Crew created successfully")
    
    print("\n📊 Crew tasks:")
    for i, task in enumerate(crew.crew().tasks, 1):
        print(f"  {i}. {task.description[:100]}...")
    
except Exception as e:
    print(f"❌ Error creating crew: {e}")
    import traceback
    traceback.print_exc()
