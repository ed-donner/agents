# import all related modules
from openai import OpenAI
import json
from pypdf import PdfReader
from environment import api_key, ai_model, resume_file, summary_file, name, ratelimit_api, request_token
from pushover import Pushover
import requests
from exception import RateLimitError


class Chatbot:
    __openai = OpenAI(api_key=api_key)

    # define tools setup for OpenAI
    def __tools(self):
        details_tools_define = {
            "user_details": {
                "name": "record_user_details",
                "description": "Usee this tool to record that a user is interested in being touch and provided an email address",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "Email address of this user"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of this user, if they provided"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Any additional information about the conversation that's worth recording to give context"
                        }
                    },
                    "required": ["email"],
                    "additionalProperties": False
                }
            },
            "unknown_question": {
                "name": "record_unknown_question",
                "description": "Always use this tool to record any question that couldn't answered as you didn't know the answer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question that couldn't be answered"
                        }
                    },
                    "required": ["question"],
                    "additionalProperties": False
                }
            }
        }

        return [{"type": "function", "function": details_tools_define["user_details"]}, {"type": "function", "function": details_tools_define["unknown_question"]}]

    # handle calling of tools
    def __handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)

            pushover = Pushover()

            tool = getattr(pushover, tool_name, None)
            # tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})

        return results



    # read pdf document for the resume
    def __get_summary_by_resume(self):
        reader = PdfReader(resume_file)
        linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                linkedin += text

        with open(summary_file, "r", encoding="utf-8") as f:
            summary = f.read()

        return {"summary": summary, "linkedin": linkedin}


    def __get_prompts(self):
        loaded_resume = self.__get_summary_by_resume()
        summary = loaded_resume["summary"]
        linkedin = loaded_resume["linkedin"]

        # setting the prompts
        system_prompt = f"You are acting as {name}. You are answering question on {name}'s website, particularly question related to {name}'s career, background, skills and experiences." \
            f"You responsibility is to represent {name} for interactions on the website as faithfully as possible." \
            f"You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions." \
            "Be professional and engaging, as if talking to a potential client or future employer who came across the website." \
            "If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career." \
            "If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool." \
            f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n" \
            f"With this context, please chat with the user, always staying in character as {name}."

        return system_prompt

    # chatbot function
    def chat(self, message, history):
        try:
            # implementation of ratelimiter here
            response = requests.post(
                ratelimit_api,
                json={"token": request_token}
            )
            status_code = response.status_code

            if (status_code == 429):
                raise RateLimitError()

            elif (status_code != 201):
                raise Exception(f"Unexpected status code from rate limiter: {status_code}")

            system_prompt = self.__get_prompts()
            tools = self.__tools();

            messages = []
            messages.append({"role": "system", "content": system_prompt})
            messages.extend(history)
            messages.append({"role": "user", "content": message})

            done = False

            while not done:
                response = self.__openai.chat.completions.create(model=ai_model, messages=messages, tools=tools)

                finish_reason = response.choices[0].finish_reason

                if finish_reason == "tool_calls":
                    message = response.choices[0].message
                    tool_calls = message.tool_calls
                    results = self.__handle_tool_calls(tool_calls=tool_calls)
                    messages.append(message)
                    messages.extend(results)
                else:
                    done = True

            return response.choices[0].message.content
        except RateLimitError as rle:
            return rle.message

        except Exception as e:
            print(f"Error: {e}")
            return f"Something went wrong! {e}"
