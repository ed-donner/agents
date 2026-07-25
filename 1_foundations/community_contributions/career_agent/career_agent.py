
import os
from dotenv import load_dotenv
from openai import OpenAI

# load env
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # base_url="https://openrouter.ai/api/v1"
)


def run():
    print("\n--- Career Talk Agent ---\n")

    # simple conversation setup
    messages = [
        {
            "role": "system",
            "content": "You are a helpful career coach. Give clear, practical advice."
        }
    ]

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["exit", "quit"]:
            print("bye 👋")
            break

        messages.append({
            "role": "user",
            "content": user_input
        })

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )

            reply = response.choices[0].message.content

            messages.append({
                "role": "assistant",
                "content": reply
            })

            print("\nAgent:", reply)

        except Exception as e:
            print(f"\nerror: {e}")


if __name__ == "__main__":
    run()