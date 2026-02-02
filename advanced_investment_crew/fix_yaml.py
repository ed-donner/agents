"""Fix placeholder variables in tasks.yaml"""

from pathlib import Path

yaml_file = Path('src/advanced_investment_crew/config/tasks.yaml')

with open(yaml_file, 'r') as f:
    content = f.read()

# Replace problematic placeholders with descriptive text
replacements = {
    'with {X} trading days of data': 'with historical trading data',
    'with {X.X}% expected return': 'with calculated expected return',
    'and {X.X}% volatility': 'and calculated volatility',
    'achieves {X.XX} risk-adjusted return': 'achieves optimal risk-adjusted return',
    'reduces risk by {XX}%': 'reduces risk significantly',
    'max loss of {XX}%': 'maximum potential loss',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(yaml_file, 'w') as f:
    f.write(content)

print("✅ tasks.yaml fixed!")
print("\nChanged:")
for old, new in replacements.items():
    print(f"  '{old}' -> '{new}'")
