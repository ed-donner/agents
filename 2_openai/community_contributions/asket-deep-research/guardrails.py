from agents import input_guardrail, output_guardrail, GuardrailFunctionOutput
from agents.run import RunContextWrapper
from agents import Agent


@input_guardrail
async def guardrail_query_safety(ctx: RunContextWrapper, agent: Agent, message: str) -> GuardrailFunctionOutput:
    if not message or not message.strip():
        return GuardrailFunctionOutput(
            output_info={"reason": "Empty query"},
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(output_info={"reason": "Query accepted"}, tripwire_triggered=False)


@input_guardrail
async def guardrail_query_relevance(ctx: RunContextWrapper, agent: Agent, message: str) -> GuardrailFunctionOutput:
    return GuardrailFunctionOutput(output_info={"reason": "Relevance check passed"}, tripwire_triggered=False)


@output_guardrail
async def guardrail_report_quality(ctx: RunContextWrapper, agent: Agent, output) -> GuardrailFunctionOutput:
    return GuardrailFunctionOutput(
        output_info={"reason": "Quality check passed (stub)"},
        tripwire_triggered=False,
    )


@output_guardrail
async def guardrail_report_safety(ctx: RunContextWrapper, agent: Agent, output) -> GuardrailFunctionOutput:
    return GuardrailFunctionOutput(
        output_info={"reason": "Safety check passed (stub)"},
        tripwire_triggered=False,
    )
