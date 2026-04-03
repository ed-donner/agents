from models.schema import RedesignProcessInput, RedesignProcessOutput

def redesign_process(input: RedesignProcessInput) -> RedesignProcessOutput:
    steps = input.original_steps.copy()
    for rec in input.recommendations:
        step_name = rec.action.replace("Add step: '", "").rstrip("'")
        if step_name not in steps:
            steps.append(step_name)
    return RedesignProcessOutput(improved_process=steps)