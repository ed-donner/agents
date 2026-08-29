from openai import OpenAI

class DigitalTwin:
    def __init__(self, provider, context):
        ok, endpoint, api_key = provider.get_provider_credentials("groq")
        if not ok:
            raise Exception("Provider not found")
        
        self.client = OpenAI(base_url=endpoint, api_key=api_key)
        self.context = context
        self.system_prompt = context.get("system_prompt")

    def prompt_agent(self, messages, tools):
        message_list = [{"role": "system", "content": self.system_prompt}] + messages

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=message_list,
            tools=tools,
            max_completion_tokens=5000,
        )
        return response
