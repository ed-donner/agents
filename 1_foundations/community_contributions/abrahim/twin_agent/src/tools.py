import json


class AiTools:
    def __init__(self, notification_client, knowledge_store):
        self.notification_client = notification_client
        self.knowledge_store = knowledge_store

    def __tool_func(self):
        return {
            "record_user_details": self.record_user_details,
            "record_unknown_question": self.record_unknown_question,
            "query_knowledge": self.query_knowledge,
        }

    def record_user_details(
        self, email, name="Name not provided", notes="not provided"
    ):
        self.notification_client.push(
            f"Recording interest from {name} with email {email} and notes {notes}"
        )
        return "OK"

    def record_unknown_question(self, question):
        self.notification_client.push(
            f"Recording {question} asked that I couldn't answer"
        )
        return "OK"

    def query_knowledge(self, question):
        results = self.knowledge_store.search(question, k=5)
        return json.dumps(
            [{"content": r["content"], "score": r["score"]} for r in results]
        )

    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}")

            # Call the corresponding tool function based on the name
            tool = self.__tool_func().get(tool_name)
            result = tool(**arguments) if tool else "No tool found"
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return results

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "record_user_details",
                    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "The email address of this user",
                            },
                            "name": {
                                "type": "string",
                                "description": "The user's name, if they provided it",
                            },
                            "notes": {
                                "type": "string",
                                "description": "Any additional info about the conversation that's worth recording to give context",
                            },
                        },
                        "required": ["email"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "record_unknown_question",
                    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question that couldn't be answered",
                            },
                        },
                        "required": ["question"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "query_knowledge",
                    "description": "Search the personal knowledge base for notes, projects, and writings beyond the LinkedIn profile. Use when the user asks about topics not covered in the linkedin profile or summary. The tool has multiple questions and answers a recruiter could ask.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question to search the knowledge base for",
                            }
                        },
                        "required": ["question"],
                        "additionalProperties": False,
                    },
                },
            },
        ]
