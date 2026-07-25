from crewai import Agent


def create_agents():
    manager = Agent(
        role="Career Manager",
        goal="Oversee the career advisory process and ensure structured output",
        backstory="An experienced career coach.",
        llm="gpt-4",
        verbose=True
    )

    researcher = Agent(
        role="Market Researcher",
        goal="Identify relevant career roles",
        backstory="Expert in job market analysis.",
        llm="gpt-4",
        verbose=True
    )

    analyst = Agent(
        role="Skill Analyst",
        goal="Identify skill gaps and learning plan",
        backstory="Expert in career development.",
        llm="gpt-4",
        verbose=True
    )

    return manager, researcher, analyst