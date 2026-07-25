from agents import Agent, WebSearchTool, ModelSettings, function_tool
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from settings import Settings
import requests

settings = Settings()




class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


def make_model(provider: str, model_name: str) -> OpenAIChatCompletionsModel:
   
    provider_clients = {
        "openai": lambda: AsyncOpenAI(
            api_key=settings.openai_api_key
        ),
        "deepseek": lambda: AsyncOpenAI(
            base_url=settings.deepseek_base_url,
            api_key=settings.deepseek_api_key
        ),
        "gemini": lambda: AsyncOpenAI(
            base_url=settings.gemini_base_url,
            api_key=settings.gemini_api_key
        ),
        "groq": lambda: AsyncOpenAI(
            base_url=settings.groq_base_url,
            api_key=settings.groq_api_key
        ),
        "openrouter": lambda: AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key
        ),
    }

    if provider not in provider_clients:
        raise ValueError(
            f"Unknown provider '{provider}'."
        )

    client = provider_clients[provider]()
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


def build_send_email_tool():
    @function_tool
    def send_email(subject: str, html_body: str) -> dict:
        
        response = requests.post(
            f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages",
            auth=("api", settings.mailgun_api_key),
            data={
                "from":    settings.mailgun_from_email,
                "to":      [settings.mailgun_recipient],
                "subject": subject,
                "html":    html_body,
            },
        )
        response.raise_for_status()
        print("Mailgun response:", response.status_code)
        return {"status": "success", "status_code": response.status_code}

    return send_email



class Tools:

    HOW_MANY_SEARCHES = 5

    def __init__(
        self,
        planner: tuple[str, str] = ("openai", "gpt-4o-mini"),
        search:  tuple[str, str] = ("openai", "gpt-4o-mini"),
        writer:  tuple[str, str] = ("openai", "gpt-4o-mini"),
        email:   tuple[str, str] = ("openai", "gpt-4o-mini"),
        manager: tuple[str, str] = ("openai", "gpt-4o-mini"),
    ):
        self.settings = Settings()

    
        self._planner_agent = self._build_planner_agent(*planner)
        self._search_agent  = self._build_search_agent(*search)
        self._writer_agent  = self._build_writer_agent(*writer)
        self._email_agent   = self._build_email_agent(*email)

        
        self.manager_agent = self._build_manager_agent(*manager)

    
    def _build_planner_agent(self, provider: str, model_name: str) -> Agent:
        return Agent(
            name="PlannerAgent",
            instructions=(
                f"You are a helpful research assistant. Given a query, come up with a set of web "
                f"searches to perform to best answer the query. "
                f"Output {self.HOW_MANY_SEARCHES} terms to query for."
            ),
            model=make_model(provider, model_name),
            output_type=WebSearchPlan,
        )

    def _build_search_agent(self, provider: str, model_name: str) -> Agent:
        
        return Agent(
            name="SearchAgent",
            instructions=(
                 "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
            ),
            tools=[WebSearchTool(search_context_size="low")],
            model=model_name,
            model_settings=ModelSettings(tool_choice="required"),
        )

    def _build_writer_agent(self, provider: str, model_name: str) -> Agent:
        return Agent(
            name="WriterAgent",
            instructions=(
                    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
            ),
            model=make_model(provider, model_name),
            output_type=ReportData,
        )

    def _build_email_agent(self, provider: str, model_name: str) -> Agent:
        return Agent(
            name="EmailAgent",
            instructions=(
                "You send nicely formatted HTML emails based on a detailed report. "
                "You will be provided with a markdown report. Use your send_email tool to send "
                "one email with the report converted into clean, well-presented HTML and an "
                "appropriate subject line."
            ),
            tools=[build_send_email_tool()],
            model=make_model(provider, model_name),
        )

    
    def _build_manager_agent(self, provider: str, model_name: str) -> Agent:
        planner_tool = self._planner_agent.as_tool(
            tool_name="planner_agent",
            tool_description=(
                "Plan the web searches needed to answer a research query. "
                "Pass the raw query; returns a structured list of search terms with reasoning."
            ),
        )
        search_tool = self._search_agent.as_tool(
            tool_name="search_agent",
            tool_description=(
                "Perform a single web search. Pass a search term and the reason for searching; "
                "returns a concise summary of the results."
            ),
        )
        writer_tool = self._writer_agent.as_tool(
            tool_name="writer_agent",
            tool_description=(
                "Write a full markdown research report. Pass the original query and all "
                "summarised search results; returns the structured report."
            ),
        )
        email_tool = self._email_agent.as_tool(
            tool_name="email_agent",
            tool_description=(
                "Convert a markdown report into a formatted HTML email and send it. "
                "Pass the full markdown report."
            ),
        )

        return Agent(
            name="ResearchManager",
            instructions=(
            "You are a research manager orchestrating a full deep-research pipeline. "
            "When given a query with clarifications already provided, follow these steps strictly in order:\n\n"
            "1. Call `planner_agent` with the full query and clarifications to produce "
            "   an intelligent, targeted list of search terms.\n"
            "2. Call `search_agent` for EACH search term from the planner to gather summaries. "
            "   Run these concurrently where possible.\n"
            "3. Call `writer_agent` with the original query, the clarifications, and ALL search "
            "   summaries to produce a detailed, focused markdown report. Important, structure and tone the final report according to the report type specified..\n"
            "4. Call `email_agent` with the finished markdown report to send it to the user.\n\n"
            "Do not skip any step. Do not write the report yourself — always delegate. "
            "After the email is sent, return the full markdown report as your final output."
            ),
            tools=[planner_tool, search_tool, writer_tool, email_tool],
            model=make_model(provider, model_name),
        )