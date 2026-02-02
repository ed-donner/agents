"""
Comprehensive fix for all placeholder variables in YAML files
"""

import re
from pathlib import Path

def fix_placeholders(file_path):
    """Remove or replace all {X} style placeholders"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Backup
    backup_path = file_path.with_suffix('.yaml.backup2')
    with open(backup_path, 'w') as f:
        f.write(content)
    
    print(f"\n📄 Processing: {file_path.name}")
    print(f"💾 Backup saved: {backup_path.name}")
    
    # Find all placeholders
    pattern = r'\{([^}]+)\}'
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        print("   ✅ No placeholders found")
        return
    
    print(f"   🔍 Found {len(matches)} placeholders:")
    
    # Replacement rules
    replacements = {
        # Specific patterns
        r'\{X\} trading days': 'historical trading days',
        r'\{X\.X\}%': 'calculated percentage',
        r'\{X\.XX\}': 'calculated value',
        r'\{XX\}%': 'significant percentage',
        r'\{X\}': 'calculated value',
        r'\{XX\}': 'calculated value',
        
        # Keep valid template variables
        # (these should be in inputs dictionary)
    }
    
    # Apply replacements
    for pattern, replacement in replacements.items():
        old_content = content
        content = re.sub(pattern, replacement, content)
        if content != old_content:
            count = len(re.findall(pattern, old_content))
            print(f"      ✓ Replaced {count}x: {pattern} -> {replacement}")
    
    # Write fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"   ✅ Fixed!")

# Fix both YAML files
config_dir = Path('src/advanced_investment_crew/config')

print("=" * 80)
print("🔧 FIXING YAML PLACEHOLDERS")
print("=" * 80)

for yaml_file in ['agents.yaml', 'tasks.yaml']:
    file_path = config_dir / yaml_file
    if file_path.exists():
        fix_placeholders(file_path)

print("\n" + "=" * 80)
print("✅ ALL PLACEHOLDERS FIXED")
print("=" * 80)
print("\nNow run: python src/advanced_investment_crew/main.py test")
