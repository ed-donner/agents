def prioritize_tasks(tasks: list):
    prioritized = sorted(tasks, key=lambda x: len(x))
    return prioritized