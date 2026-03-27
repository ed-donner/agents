from agents import input_guardrail, output_guardrail, GuardrailFunctionOutput

@input_guardrail
async def check_skill_input(ctx, agent, message):
    # check if skill name is reasonable length
    # reject very short inputs that are likely invalid
    if len(message.strip()) < 3:
        return GuardrailFunctionOutput(
            output_info={"reason": "skill name too short"},
            tripwire_triggered=True
        )
    return GuardrailFunctionOutput(
        output_info={},
        tripwire_triggered=False
    )

@output_guardrail
async def check_learning_path_quality(ctx, agent, output):
    # validate learning path has meaningful content
    # check minimum content length to ensure quality
    if hasattr(output, 'content') and len(output.content) < 100:
        return GuardrailFunctionOutput(
            output_info={"reason": "content too short"},
            tripwire_triggered=True
        )
    return GuardrailFunctionOutput(
        output_info={},
        tripwire_triggered=False
    )
