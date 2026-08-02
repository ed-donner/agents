from functools import partial

from crewai import Task

from engineering_team.models import SystemArchitecture


def on_architecture_complete(team, output):
    architecture = output.pydantic or SystemArchitecture.model_validate(output.to_dict())
    state = team.runtime
    state["architecture"] = architecture
    state["modules_by_name"] = {module.name: module for module in architecture.modules}
    ready = [name for name in architecture.build_order if not state["modules_by_name"][name].depends_on]
    if not ready:
        raise ValueError("The architecture must include at least one dependency-free module")
    for module_name in ready:
        _schedule_module(team, module_name)


def on_module_complete(team, module_name, output):
    state = team.runtime
    if module_name in state["completed_modules"]:
        return
    state["completed_modules"].add(module_name)
    _add_task(team, _create_test_task(team, module_name))
    for ready_module in _ready_modules(team):
        _schedule_module(team, ready_module)
    if len(state["completed_modules"]) == len(state["architecture"].modules):
        on_all_modules_complete(team, output)


def on_all_modules_complete(team, _output):
    state = team.runtime
    if state["final_task_created"]:
        return
    state["final_task_created"] = True
    _add_task(team, _create_app_task(team))


def _add_task(team, task):
    crew = team.runtime["crew"]
    if hasattr(crew, "add_task"):
        crew.add_task(task)
        return
    crew.tasks.append(task)


def _ready_modules(team):
    state = team.runtime
    return [
        name
        for name in state["architecture"].build_order
        if name not in state["scheduled_modules"]
        and set(state["modules_by_name"][name].depends_on).issubset(state["completed_modules"])
    ]


def _schedule_module(team, module_name):
    state = team.runtime
    task = _create_module_task(team, module_name)
    state["scheduled_modules"].add(module_name)
    state["module_tasks"][module_name] = task
    _add_task(team, task)


def _create_module_task(team, module_name):
    state = team.runtime
    module = state["modules_by_name"][module_name]
    dependencies = [state["module_tasks"][name] for name in module.depends_on]
    return Task(
        name=f"build_{_stem(module.name)}",
        description=_module_description(team, module),
        expected_output=f"Raw Python code for {module.name}.",
        agent=team.backend_engineer(),
        context=[state["architecture_task"], *dependencies],
        output_file=f"output/{module.name}",
        callback=partial(on_module_complete, team, module.name),
    )


def _create_test_task(team, module_name):
    module_task = team.runtime["module_tasks"][module_name]
    return Task(
        name=f"test_{_stem(module_name)}",
        description=_test_description(team, module_name),
        expected_output=f"Raw Python tests for {module_name}.",
        agent=team.test_engineer(),
        context=[module_task],
        output_file=f"output/test_{module_name}",
    )


def _create_app_task(team):
    state = team.runtime
    module_tasks = [state["module_tasks"][name] for name in state["architecture"].build_order]
    return Task(
        name="build_app",
        description=_app_description(team),
        expected_output="Raw Python code for app.py.",
        agent=team.integration_engineer(),
        context=[state["architecture_task"], *module_tasks],
        output_file="output/app.py",
    )


def _module_description(team, module):
    classes = ", ".join(module.classes) or "None"
    functions = ", ".join(module.functions) or "None"
    dependencies = ", ".join(module.depends_on) or "None"
    requirements = team.runtime["inputs"]["requirements"]
    return (
        f"Implement {module.name} for this e-commerce system: {requirements}\n"
        f"Module description: {module.description}\n"
        f"Classes: {classes}\n"
        f"Functions: {functions}\n"
        f"Dependencies available in context: {dependencies}\n"
        "Output only raw Python code."
    )


def _test_description(team, module_name):
    requirements = team.runtime["inputs"]["requirements"]
    return (
        f"Write unit tests for {module_name} in this e-commerce system: {requirements}\n"
        "Use the backend module in context and output only raw Python code."
    )


def _app_description(team):
    requirements = team.runtime["inputs"]["requirements"]
    return (
        f"Build a Gradio app.py for this e-commerce system: {requirements}\n"
        "Use the backend modules in context, wire together the available flows, and output only raw Python code."
    )


def _stem(module_name):
    return module_name[:-3] if module_name.endswith(".py") else module_name
