#!/usr/bin/env python
import warnings
from homeworker.crew import Homework
from dotenv import load_dotenv
from crewai import Task, Crew, Process
import json

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

VERBOSE=False
# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run(grade: str, to_email: str, topic: str):
    """
    Run the crew.
    """
    inputs = {
        "grade": grade,
        "to_email": to_email,
        "topic": topic
    }
    hw = Homework()
    # 1. Run principal task to get tutor selection
    principal_task = Task(
        config=hw.tasks_config['principal_task'],
        agent=hw.principal()
    )

    crew = Crew(
        agents=[hw.principal()],
        tasks=[principal_task],
        process=Process.sequential,
        verbose=VERBOSE
    )

    principal_result = crew.kickoff(inputs=inputs)
    selected_tutor = json.loads(principal_result.raw)['selected_tutor']

    # 2. Choose the correct tutor task
    if selected_tutor == "maths_tutor":
        tutor_task = Task(
            config=hw.tasks_config['create_math_homework'],
            agent=hw.maths_tutor()
        )
        tutor_agent=hw.maths_tutor()
    elif selected_tutor == "english_tutor":
        tutor_task = Task(
            config=hw.tasks_config['create_english_homework'],
            agent=hw.english_tutor()
        )
        tutor_agent=hw.english_tutor()
    else:
        tutor_task = Task(
            config=hw.tasks_config['create_general_homework'],
            agent=hw.general_tutor()
        )
        tutor_agent=hw.general_tutor()

    assignment_crew = Crew(
        agents=[tutor_agent],
        tasks=[tutor_task],
        process=Process.sequential,
        verbose=VERBOSE
    )

    assignment_crew.kickoff(inputs=inputs)

    # 3. Compose email task
    compose_task = Task(
        config=hw.tasks_config['compose_email'],
        agent=hw.mail_composer()
    )

    compose_crew = Crew(
        agents=[hw.mail_composer()],
        tasks=[compose_task],
        process=Process.sequential,
        verbose=VERBOSE
    )

    compose_crew.kickoff(inputs=inputs)

    # 4. Send email task
    send_task = Task(
        config=hw.tasks_config['send_email'],
        agent=hw.mailer()
    )

    email_crew = Crew(
        agents=[hw.mailer()],
        tasks=[send_task],
        process=Process.sequential,
        verbose=VERBOSE
    )
    try:
        result = email_crew.kickoff(inputs=inputs)
        result_str = str(getattr(result, "raw", result.raw))  # Use .raw if available, else str(result)
        if "unauthorized" in result_str.lower():
            return f"Mailer failed: Unauthorized. Crew completed with errors. Used {selected_tutor} to generate assignment"
        return f"Crew completed successfully. Used {selected_tutor} to generate assignment"
    except Exception as e:
        return f"Crew failed: {str(e)}"
    
if __name__ == "__main__":
    run()
