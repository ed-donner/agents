"""
HALI — HPV Awareness & Learning Initiative
Main Gradio app — agent loop + dual-mode UI.
"""

from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

from evaluator import evaluate, rerun
from prompts import CAREGIVER_SYSTEM_PROMPT, CHW_SYSTEM_PROMPT
from tools import TOOLS, handle_tool_calls

load_dotenv(override=True)
client = OpenAI()


# Agent loop

def chat(message: str, history: list, mode: str = "caregiver") -> str:
    """
    Core agent loop (Lab 4/5 pattern):
    1. Call LLM with tools
    2. If it requests a tool — run it, feed result back, loop
    3. When it replies normally — evaluate (Lab 3 pattern)
    4. If evaluation fails — rerun with feedback
    """
    system_prompt = CAREGIVER_SYSTEM_PROMPT if mode == "caregiver" else CHW_SYSTEM_PROMPT
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]

    done = False
    while not done:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
        )
        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls":
            message_obj = response.choices[0].message
            results = handle_tool_calls(message_obj.tool_calls)
            messages.append(message_obj)
            messages.extend(results)
        else:
            done = True

    reply = response.choices[0].message.content

    evaluation = evaluate(reply, message, history)
    if evaluation.is_acceptable:
        print("Passed evaluation")
    else:
        print(f"Failed evaluation: {evaluation.feedback}")
        reply = rerun(reply, message, history, evaluation.feedback, system_prompt)

    return reply


def chat_caregiver(message: str, history: list) -> str:
    return chat(message, history, mode="caregiver")


def chat_chw(message: str, history: list) -> str:
    return chat(message, history, mode="chw")


# Gradio UI

with gr.Blocks(title="HALI — HPV Kenya") as demo:
    gr.Markdown(
        """# HALI — Health & Wellbeing
### HPV Vaccine Companion for Kenya

Helping families and health workers understand and access HPV vaccination.
Cervical cancer kills **3,400 Kenyan women every year**. The vaccine is **free, safe, and one dose is enough.**
"""
    )

    with gr.Tabs():
        with gr.Tab("For Families (Caregivers)"):
            gr.Markdown(
                "Ask HALI anything about the HPV vaccine — in English or Swahili. "
                "No question is too small or too sensitive."
            )
            gr.ChatInterface(
                fn=chat_caregiver,
                type="messages",
                examples=[
                    "I heard this vaccine makes girls unable to have babies. Is this true?",
                    "My daughter is 13. Is she eligible for the vaccine?",
                    "Where can I get the vaccine in Garissa?",
                    "Our imam says we should not take it. What do you say?",
                ],
            )

        with gr.Tab("For Health Workers (CHW)"):
            gr.Markdown(
                "Clinical support for Community Health Workers in the field. "
                "Get evidence-based talking points and log hesitant families for follow-up."
            )
            gr.ChatInterface(
                fn=chat_chw,
                type="messages",
                examples=[
                    "A mother in Mandera refuses — says it's haram. How do I respond?",
                    "What is the evidence behind the single-dose schedule change?",
                    "A girl aged 16 missed the school programme. Is she still eligible?",
                    "How do I handle a parent who says the government put something dangerous in it?",
                ],
            )

if __name__ == "__main__":
    demo.launch()
