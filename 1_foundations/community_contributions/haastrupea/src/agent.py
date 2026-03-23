from openai import OpenAI
import json

from src.tools import Tools

class Agent:
    def __init__(self, llm_client: OpenAI, tools: Tools, name: str, model: str = "gpt-4o-mini") -> None:
        self.tools = tools
        self.name = name
        self.llm_client = llm_client
        self.model = model
        
    def get_system_prompt (self, contexts: list[dict]):
        name = self.name
        system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
        particularly questions related to {name}'s career, background, skills and experience. \
        Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
        You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. \
        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        if contexts:
            system_prompt += "\n## Retrieved Information:\n"
            for doc in contexts:
                system_prompt += f"\n[{doc['source']}]:\n{doc['text']}\n"

        return system_prompt

    def handle_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            tool_fn = getattr(self.tools, tool_name, None)
            result = tool_fn(**arguments) if tool_fn else {"error": f"Unknown tool: {tool_name}"}
            print(f"[TOOL-CALL] Tool called: {tool_name}", flush=True)
            
            results.append({ "role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id })
        return results

    def llm_call(self, messages,  contexts: list[dict] ) -> str:

        system_prompt = self.get_system_prompt(contexts)

        messages = [{"role": "system", "content": system_prompt}] + messages

        tools = self.tools.get_tools()
        done = False
        while not done:
            response = self.llm_client.chat.completions.create(model=self.model, messages=messages, tools= tools, temperature=0.5)
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
                return response.choices[0].message.content
        
        return response.choices[0].message.content

    def should_use_rag_with_Query(self, message):
            query_check = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Is this query asking for specific information about someone's background, experience, or skills? Answer only 'yes' or 'no'.\n\nQuery: {message}"}],
                temperature=0
            )
            should_retrieve = query_check.choices[0].message.content.strip().lower() == "yes"
            
            return should_retrieve