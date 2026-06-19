from crewai import Task
from data.roles import ROLE_SKILLS


def create_tasks(user_input, manager, researcher, analyst):

    research_task = Task(
        description=f"""
        Based on the user's goal: {user_input['goal']},
        identify relevant career roles from this dataset:
        {list(ROLE_SKILLS.keys())}

        Return a list of roles.
        """,
        agent=researcher,
        expected_output="List of relevant career roles"
    )

    analysis_task = Task(
        description=f"""
        The user has these skills: {user_input['skills']}

        For each role identified previously, compare required skills
        with user skills and identify gaps.

        Then generate a simple learning plan.

        Use this dataset:
        {ROLE_SKILLS}
        """,
        agent=analyst,
        expected_output="Skill gaps and learning plan"
    )

    final_task = Task(
        description="""
        Combine all findings into a structured report:

        1. Recommended Roles
        2. Skill Gaps
        3. Learning Plan

        Ensure the output is clean and well formatted.
        """,
        agent=manager,
        expected_output="Final structured career report"
    )

    return [research_task, analysis_task, final_task]