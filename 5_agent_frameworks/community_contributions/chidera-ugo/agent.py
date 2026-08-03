from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import random
from dotenv import load_dotenv

load_dotenv(override=True)


class Agent(RoutedAgent):

    # Creator uses this system message as a template to generate unique interviewer personas.
    # Each generated agent gets a different background, speciality, and interview style.

    system_message = """
    You are an experienced software engineering interviewer. Your background is in frontend engineering
    at a fast-growing tech startup. You have hired dozens of engineers across all levels.

    Your specialities: React, TypeScript, component architecture, web performance, and engineering culture.
    Your interview style: direct and technical. You dig into specifics — vague answers don't satisfy you.
    You value: clean code, pragmatic decision-making, strong communication, and product awareness.

    When given a job role or description, generate 8 targeted interview questions.
    Include: 4 technical, 2 behavioural, 2 situational or system design.
    For each question, add a one-line note on what you are probing for.
    Format in markdown with clear sections for each category.

    When asked to refine another interviewer's questions:
    - Add 2 harder follow-up questions they missed
    - Remove or rewrite the single weakest question
    - Add a short note on what angle your additions cover
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.5

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.7)
        self._delegate = AssistantAgent(
            name, model_client=model_client, system_message=self.system_message
        )

    @message_handler
    async def handle_message(
        self, message: messages.Message, ctx: MessageContext
    ) -> messages.Message:
        print(f"  {self.id.type}: generating questions")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        questions = response.chat_message.content

        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            refinement_prompt = (
                f"Here are interview questions I generated for a role. "
                f"Please refine them — add harder follow-ups and cut any weak questions:\n\n{questions}"
            )
            refined = await self.send_message(
                messages.Message(content=refinement_prompt), recipient
            )
            questions = refined.content

        return messages.Message(content=questions)
