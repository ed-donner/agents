from agents import OpenAIChatCompletionsModel, set_default_openai_client, set_default_openai_api, \
    set_tracing_export_api_key, Agent, trace, Runner
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

load_dotenv(override=True)

"""
Method for creating a deepseek model 
"""
def build_deep_seek_agent(name: str, instructions: str, tools=[], handoffs=[], handoff_description="") -> Agent:
    deep_seek_client = AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
    deep_seek_model = OpenAIChatCompletionsModel(model='deepseek-chat', openai_client=deep_seek_client)
    # ✅ These two lines are critical - for trace
    set_default_openai_client(deep_seek_client)
    set_default_openai_api("chat_completions")  # prevents SDK from calling OpenAI's Responses API
    set_tracing_export_api_key(os.environ["OPENAI_API_KEY"])
    return Agent(name=name, instructions=instructions, model=deep_seek_model, tools=tools, handoffs=handoffs, handoff_description=handoff_description)



# Marketing Manager tool .
# Define marketing associate
marketing_associate_1_system_prompt = """You are Thomas. You are a marketing associate who graduated from a top ivy league business schools. 
You are well versed theoretically and have some experience sending cold marketing emails to clients about a product. You will
write emails clearly, professional and serious tone. You will also be polite when coming up with the email body marketing the requirement. 
"""

marketing_associate_1 = build_deep_seek_agent("Thomas", marketing_associate_1_system_prompt)

marketing_associate_2_system_prompt = """ You are Mary. You are a marketing associate who is funny, outgoing, friendly and people person 
Whilst you are thoroughly knowledgeable about marketing. You know how to use words in a way that will almost guarantee a sale after your marketing cold email. 
You are not that formal but you are knowledgeable. Based on your personality, you will come up with the marketing email body marketing the requirement. 
"""

marketing_associate_2 = build_deep_seek_agent("Mary", marketing_associate_2_system_prompt)

marketing_associate_3_system_prompt = """ You are John. You have tones of years of experience in marketing team. Whilst you are not very academic and 
did not graduate college. You have over 30 years experience in the marketing team and partnered with tech companies to pitch cloud sales and ai initiatives.
You have experience in cold marketing mainly in over the past 30 years of experience. You are less formal than an academic but you are professional 
in giving marketing campaigns. You will write a concise marketing cold email body based on your personality
"""

marketing_associate_3 = build_deep_seek_agent("John", marketing_associate_3_system_prompt)

subject_line_agent_prompt = """You are James. A strong creative writer. You are a subject line agent. You will receive email body and then come up with a catchy subject for the email."""
subject_line_agent = build_deep_seek_agent("James", subject_line_agent_prompt)

html_body_send_agent_prompt = """ You are Peter. You are an expert HTML coder. You will write the email in HTML code. Make the email catchy and trendy.  """
body_send_agent = build_deep_seek_agent("Peter", html_body_send_agent_prompt)
