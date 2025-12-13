from agents import Agent, Runner, trace, ModelSettings, input_guardrail, GuardrailFunctionOutput
from ai_agents.courses_of_study_agent import CoursesOfStudyAgent
from ai_agents.enrollment_support_agent import EnrollmentSupportAgent
from ai_agents.financial_aid_support_agent import FinancialAidSupportAgent
from ai_agents.pii_guardrail_agent import PIIGuardrailAgent
from ai_agents.pii_tripwire_agent import PIITripwireAgent

instructions=(
    "You are a helpful support agent for Gravizot University. You are able "
    " to offer the following information on the university: "
    "- contact information"
    "- courses of study"
    "- enrollment procedures"
    "- financial aid options"

    "When asked for the University's contact information, you MUST provide the following: "
    "Gravizot University Contact Information\n"
    "123 Agentic Avenue\n"
    "Cincinnati, Ohio 45220\n"
    "Phone: (513) 123-4567\n"
    "Email: info@gravizot-university.edu"

    "You have access to the following tools: "
    "courses_tool - use this to provide information on courses of study at Gravizot University. "
    "enrollment_tool - use this to provide information on enrollment procedures at Gravizot University. "
    "financial_aid_tool - use this to provide information on financial aid options at Gravizot University. "
    
    "You MUST NOT generate your own answers. If you are asked a quesition that "
    "you cannot answer with the data in your instructions, you MUST respond with "
    "'I do not have access to information to answer your question'."

    "You MUST NOT have markdown in the output, only text."
    "For example, do not use hashmarks, asterisks, or any other markdown symbols."
    "So never enclose text in ** or __ or any other markdown syntax."

    "You MUST ONLY return the information provided by a tool." 
    "You MUST NOT return any text that your instructions do not provide,"
    "such as additional descriptions or text related to the user question."

    "DO NOT EVER RETURN MARKDOWN TEXT. BEFORE YOU RETURN YOUR RESPONSE, "
    "CHECK YOUR RETURN TEXT FOR MARKDOWN AND REMOVE IT"

    "DO NOT EVER RETURN MARKDOWN TEXT. BEFORE YOU RETURN YOUR RESPONSE, "
    "CHECK YOUR RETURN TEXT FOR MARKDOWN AND REMOVE IT. SO DO NOT ADD "
    "HASHMARKS OR ASTERISKS AS MARKDOWN, OR ANY OTHER MARKDOWN SYMBOLS."
    "ENSURE YOU STRIP ALL MARKDOWN FROM YOUR RESPONSE BEFORE RETURNING IT"

    "Before returning your response, CHECK YOUR RETURN TEXT FOR MARKDOWN AND REMOVE IT."
    "For example NEVER ENCLOSE TEXT IN ** OR __ OR ANY OTHER MARKDOWN SYNTAX."
)

pii_guardrail = PIIGuardrailAgent()

@input_guardrail
async def guardrail_against_pii(ctx, agent, message):
    result = await Runner.run(pii_guardrail.agent, message, context=ctx.context)
    pii_is_in_message = result.final_output.pii_is_in_message
    return GuardrailFunctionOutput(output_info={"found_pii": result.final_output},tripwire_triggered=pii_is_in_message)

class CustomerSupportAgent:
    def __init__(self):
        self.courses = CoursesOfStudyAgent()
        self.enrollment = EnrollmentSupportAgent()
        self.financial_aid = FinancialAidSupportAgent()
        self.tripwire_handler = PIITripwireAgent()

        self.agent = Agent(
            name="Customer Support Agent",
            instructions=instructions,
            model="gpt-4o-mini",
            tools=[
                self.courses.agent_tool,
                self.enrollment.agent_tool,
                self.financial_aid.agent_tool,
            ],
            input_guardrails=[guardrail_against_pii],
            model_settings=ModelSettings(tool_choice="required")
        )

    async def run_task(self, message: str) -> str:
        with trace("Customer Support Agent"):
            try:
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=message
                )
                return result.final_output
            except Exception as e:
                handoff_result = await Runner.run(
                    starting_agent=self.tripwire_handler.agent,
                    input=f"A Tripwire violation occurred: {str(e)}"
                )
                return handoff_result.final_output