import yaml

with open('src/advanced_investment_crew/config/tasks.yaml', 'r') as f:
    tasks = yaml.safe_load(f)

print("✅ YAML syntax DOĞRU!")
print(f"📊 Toplam {len(tasks)} task:")
for task_name, task_config in tasks.items():
    if isinstance(task_config, dict):
        agent = task_config.get('agent', 'N/A')
        print(f"  ✅ {task_name} -> agent: {agent}")
    else:
        print(f"  ⚠️ {task_name} is not a dict, got {type(task_config)}")
