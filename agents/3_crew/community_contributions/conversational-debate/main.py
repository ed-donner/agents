from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai.memory import LongTermMemory
from agents import proposer, opposer, judge
import gradio as gr
from gradio import themes
import time

def format_as_chat(message, chat_history=[], role="user"):
    chat_history.append({"role": role, "content": message})
    return chat_history


def format_as_chat_history(messages):
    return [
        {"role": "user" if i % 2 == 0 else "assistant", "content": message}
        for i, message in enumerate(messages)
    ]


def debate(motion="Being vegan is better for the environment", MAX_ROUNDS=4):
    print("Hello from debate-prep-ai!")
    load_dotenv(override=True)

    turn = "proposer"
    debate_log = []
    yield format_as_chat("Starting debate...", [], "assistant")

    print("Iterating now...")
    for round_num in range(MAX_ROUNDS):
        if turn == "proposer":
            prompt = (
                f"Start the debate by making your first argument supporting: '{motion}'."
                if not debate_log
                else f"The opponent said: '{debate_log[-1]}'. Respond with a strong counterargument supporting the motion. here is the entire debate log: {debate_log}"
            )
            agent = proposer
            expected_output = (
                f"A single sentence argument in favor of the motion: {motion}"
            )
        else:
            prompt = f"The opponent said: '{debate_log[-1]}'. Respond with a strong counterargument against the motion. here is the entire debate log: {debate_log}"
            agent = opposer
            expected_output = f"A single sentence argument against the motion: {motion}"

        task = Task(description=prompt, expected_output=expected_output, agent=agent)

        result = Crew(agents=[agent], tasks=[task]).kickoff()
        # print(result.raw)
        message = f"## {turn.capitalize()}: \n{result}"
        debate_log.append({"role": "assistant" if round_num % 2 ==0 else "user", "content": ""})
        for character in message:
            debate_log[-1]['content'] += character
            time.sleep(0.005)
            yield debate_log

        turn = "proposer" if turn == "opposer" else "opposer"

    # Final Verdict by Judge
    debate_summary = "\n\n".join(
        [
            (f"proposer: {point}" if i % 2 == 0 else f"opposer: {point}")
            for i, point in enumerate(debate_log)
        ]
    )
    yield format_as_chat(
        f"********************************\n\n ### Arguments Completed. \n\n Judging now ...\n\n********************************", debate_log, "assistant"
    )

    judge_task = Task(
        description=(
            f"You are the judge of a debate on the motion: '{motion}'. "
            f"Here is the full transcript of the debate:\n\n{debate_summary}\n\n"
            "Evaluate the arguments and give a reasoned verdict on which side was more persuasive and why. Respond with an organized markdown with the following sections: \n\n"
            "1. Introduction: \n\n"
            "2. Arguments: \n\n"
            "3. Conclusion: \n\n"
            "4. Verdict: \n\n"
            "5. Why: \n\n"
        ),
        expected_output="A reasoned verdict on which side was more persuasive and why.",
        agent=judge,
    )

    final_crew = Crew(tasks=[judge_task], agents=[judge], verbose=True)
    verdict = final_crew.kickoff()

    debate_log.append({"role": "assistant", "content": ""})
    for character in f"👨‍⚖️ FINAL VERDICT ARRIVED\n\n\n\n {verdict}":
        debate_log[-1]['content'] += character
        time.sleep(0.005)
        yield debate_log


def renderInterface():
    with gr.Blocks(theme=themes.Default(primary_hue="blue")) as demo:
        gr.Markdown("# Debate Prep AI")
        gr.Markdown(
            "This is a simple Agentic-AI developed using CrewAI that helps you prepare for a debate. It uses 3 agents: the proposer, the opposer and the judge. Use this app to understand what arguments (and counter-arguments) you can place during the debate."
        )
        gr.Markdown("## How to use:")
        gr.Markdown("1. Enter the motion of the debate in the text box below.")
        gr.Markdown("2. Click the 'Debate' button to start the debate.")
        gr.Markdown(
            "3. The AI will generate arguments for your side and evaluate the arguments of the other side."
        )
        gr.Markdown(
            "4. The AI will give you a verdict on which side was more persuasive and why."
        )
        gr.Markdown(
            "5. Confused where to begin? Try asking `AI is bad for humans` and click on *Debate* button."
        )

        motion = gr.Textbox(
            label="Motion",
            placeholder="What do you want to debate about?",
            info="This is the motion of the debate. It is the statement that you want to debate about. For e.g. you could say Being vegan is better for the environment",
            submit_btn="Debate",
        )
        max_rounds = gr.Slider(
            label="Number of Rounds",
            value=4,
            minimum=1,
            maximum=10,
            info="This is the number of rounds of the debate. The more rounds, the more detailed the debate will be.",
            visible=False,
        )
        chat = gr.Chatbot(label="Debate Log", value=[], type="messages")
        motion.submit(debate, inputs=[motion, max_rounds], outputs=[chat])

    demo.launch()


if __name__ == "__main__":
    renderInterface()
