import json

from openai import OpenAI
from context import TWIN_SYSTEM_PROMPT, GET_EVALUATOR_PROMPT
from tools import tools, handle_tool_calls
from styles import CSS, JS, EXAMPLES
from dotenv import load_dotenv
import gradio as gr

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"
MODEL_EVALUATOR_NAME = "gpt-5.4-nano"

openai = OpenAI()

system = [{"role": "system", "content": TWIN_SYSTEM_PROMPT}]

def evaluate_response(user_message, assistant_response):
  evaluator_prompt = GET_EVALUATOR_PROMPT(user_message=user_message, assistant_response=assistant_response)
  
  messages = [{"role": "system", "content": evaluator_prompt}]
  response = openai.chat.completions.create(model=MODEL_EVALUATOR_NAME, messages=messages)
  return json.loads(response.choices[0].message.content)


def chat(message, history):
    messages = [system] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)

    while response.choices[0].finish_reason=="tool_calls":
      message = response.choices[0].message
      
      results = handle_tool_calls(message.tool_calls)
      messages.append(message)
      messages.extend(results)
      response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
          
    final_response = response.choices[0].message.content

    evaluation = evaluate_response(message, final_response)
    if not evaluation["approved"]:
        feedback = evaluation["feedback"]

        messages.append({
            "role": "assistant",
            "content": final_response
        })

        messages.append({
            "role": "system",
            "content": (
                "Improve your previous response based on this evaluator "
                f"feedback: {feedback}. "
                "The final response must be strictly related to work."
            )
        })

        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools
        )

        final_response = response.choices[0].message.content

    return final_response


if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title="Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False),
    ).launch(css=CSS, js=JS, theme=gr.themes.Base())
