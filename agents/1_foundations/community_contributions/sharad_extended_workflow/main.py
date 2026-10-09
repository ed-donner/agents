import os
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

class EvaluationResult(BaseModel):
    result: str
    feedback: str

def router_llm(user_input):
    messages = [
        {"role": "system", "content": (
            "You are a router. Decide which task the following input is for:\n"
            "- Math: If it's a math question.\n"
            "- Translate: If it's a translation request.\n"
            "- Summarize: If it's a request to summarize text.\n"
            "Reply with only one word: Math, Translate, or Summarize."
        )},
        {"role": "user", "content": user_input}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content.strip().lower()

def math_llm(user_input):
    messages = [
        {"role": "system", "content": "You are a helpful math assistant."},
        {"role": "user", "content": f"Solve the following math problem: {user_input}"}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content.strip()

def translate_llm(user_input):
    messages = [
        {"role": "system", "content": "You are a helpful translator from English to French."},
        {"role": "user", "content": f"Translate this to French: {user_input}"}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content.strip()

def summarize_llm(user_input):
    messages = [
        {"role": "system", "content": "You are a helpful summarizer."},
        {"role": "user", "content": f"Summarize this: {user_input}"}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content.strip()

def evaluator_llm(task, user_input, solution):
    """
    Evaluates the solution. Returns (result: bool, feedback: str)
    """
    messages = [
        {"role": "system", "content": (
            f"You are an expert evaluator for the task: {task}.\n"
            "Given the user's request and the solution, decide if the solution is correct and helpful.\n"
            "Please evaluate the response, replying with whether it is right or wrong and your feedback for improvement."
        )},
        {"role": "user", "content": f"User request: {user_input}\nSolution: {solution}"}
    ]
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=messages,
        response_format=EvaluationResult
    )
    return response.choices[0].message.parsed

def generate_solution(task, user_input, feedback=None):
    """
    Calls the appropriate generator LLM, optionally with feedback.
    """
    if feedback:
        user_input = f"{user_input}\n[Evaluator feedback: {feedback}]"
    if "math" in task:
        return math_llm(user_input)
    elif "translate" in task:
        return translate_llm(user_input)
    elif "summarize" in task:
        return summarize_llm(user_input)
    else:
        return "Sorry, I couldn't determine the task."

def main():
    user_input = input("Enter your request: ")
    task = router_llm(user_input)
    max_attempts = 3
    feedback = None

    for attempt in range(max_attempts):
        solution = generate_solution(task, user_input, feedback)
        response = evaluator_llm(task, user_input, solution)
        if response.result.lower() == "right":
            print(f"Result (accepted on attempt {attempt+1}):\n{solution}")
            break
        else:
            print(f"Attempt {attempt+1} rejected. Feedback: {response.feedback}")
    else:
        print("Failed to generate an accepted solution after several attempts.")
        print(f"Last attempt:\n{solution}")

if __name__ == "__main__":
    main()
