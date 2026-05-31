from crewai import Crew
from agents import create_agents
from tasks import create_tasks


def build_crew(user_input):
    manager, researcher, analyst = create_agents()
    tasks = create_tasks(user_input, manager, researcher, analyst)

    crew = Crew(
        agents=[manager, researcher, analyst],
        tasks=tasks,
        # process="hierarchical",
        verbose=True
    )

    return crew