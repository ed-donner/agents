from crewai import Crew, Process
from leadership_calibration.crew import LeadershipCalibration



def run_single_task(agent, task, inputs):
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff(inputs=inputs)

    return result.raw if hasattr(result, "raw") else str(result)


def run_debate(topic: str):
    crew_instance = LeadershipCalibration()

    inputs = {
        "topic": topic
    }

    result = crew_instance.crew().kickoff(inputs=inputs)
    # ✅ Extract proper text from CrewOutput
    if hasattr(result, "raw"):
        return result.raw
    elif hasattr(result, "output"):
        return result.output
    else:
        return str(result)


def run_debate_stream(topic: str, state):
    state["cancelled"] = False

    yield "⏳ Initializing debate...", state

    crew_instance = LeadershipCalibration()
    inputs = {"topic": topic}

    # ----- TASK 1 -----
    if state["cancelled"]:
        yield "❌ Debate cancelled.", state
        return

    yield "🧠 Technical Architect is presenting position...\n", state

    result1 = run_single_task(
        crew_instance.senior_architect_agent(),
        crew_instance.architect_position_statement(),
        inputs
    )

    text1 = result1.raw if hasattr(result1, "raw") else str(result1)

    yield f"## 🧠 Technical Architect\n\n{text1}\n\n---\n", state

    # ----- TASK 2 -----
    if state["cancelled"]:
        yield "❌ Debate cancelled.", state
        return

    yield "🤝 Engineering Manager responding...\n", state

    result2 = run_single_task(
        crew_instance.engineering_manager_agent(),
        crew_instance.engineering_manager_position_statement(),
        inputs
    )

    text2 = result2.raw if hasattr(result2, "raw") else str(result2)

    yield f"## 🤝 Engineering Manager\n\n{text2}\n\n---\n", state

    # ----- TASK 3 -----
    if state["cancelled"]:
        yield "❌ Debate cancelled.", state
        return

    yield "⚖️ Synthesizing final resolution...\n", state

    result3 = run_single_task(
        crew_instance.senior_architect_agent(),
        crew_instance.final_alignment_and_resolution(),
        inputs
    )

    text3 = result3.raw if hasattr(result3, "raw") else str(result3)

    yield f"# ⚖️ Final Resolution\n\n{text3}\n\n✅ Debate completed.", state


def cancel_debate(state):
    state["cancelled"] = True
    return state
