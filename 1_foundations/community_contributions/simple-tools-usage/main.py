from dotenv import load_dotenv
from openai import OpenAI
import re, json

load_dotenv(override=True)
openai = OpenAI()

call_to_action = "Type something to manipulate, or 'exit' to quit."

def smart_capitalize(word):
    for i, c in enumerate(word):
        if c.isalpha():
            return word[:i] + c.upper() + word[i+1:].lower()
    return word  # no letters to capitalize

def manipulate_string(input_string):
    input_string = input_string[::-1]
    words = re.split(r'\s+', input_string.strip())
    capitalized_words = [smart_capitalize(word) for word in words]
    return ' '.join(capitalized_words)

manipulate_string_json = {
    "name": "manipulate_string",
    "description": "Use this tool to reverse the characters in the text the user enters, then to capitalize the first letter of each reversed word)",
    "parameters": {
        "type": "object",
        "properties": {
            "input_string": {
                "type": "string",
                "description": "The text the user enters"
            }
        },
        "required": ["input_string"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": manipulate_string_json}]

TOOL_FUNCTIONS = {
    "manipulate_string": manipulate_string
}

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        tool = TOOL_FUNCTIONS.get(tool_name)
        result = tool(**arguments) if tool else {}

        # Remove quotes if result is a plain string
        content = result if isinstance(result, str) else json.dumps(result)

        results.append({
            "role": "tool",
            "content": content,
            "tool_call_id": tool_call.id
        })
    return results

system_prompt = f"""You are a helpful assistant who takes text from the user and manipulates it in various ways.
Currently you do the following:
- reverse the string the user entered
- convert to all lowercase letters so any words whose first letters were capitalized are now lowercase
- convert the first letter of each word in the reversed string to uppercase
Be professional, friendly and engaging, as if talking to a customer who came across your service.
Do not output any additional text, just the result of the string manipulation.
After outputting the text, prompt the user for the next input text with {call_to_action}
With this context, please chat with the user, always staying in character.
"""

def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    done=False
    while not done:
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls":
            message = response.choices[0].message
            tool_calls = message.tool_calls
            results = handle_tool_calls(tool_calls)
            messages.append(message)
            messages.extend(results)
        else:
            done = True
    return response.choices[0].message.content

def main():
    print("\nWelcome to the string manipulation chat!")
    print(f"{call_to_action}\n")
    history = []

    while True:
        user_input = input("")
        if user_input.lower() in {"exit", "quit"}:
            print("\nThanks for using our service!")
            break

        response = chat(user_input, history)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        print(response)

if __name__ == "__main__":
    main()
