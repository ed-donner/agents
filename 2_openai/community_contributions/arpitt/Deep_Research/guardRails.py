from dotenv import load_dotenv
from agents import Agent, Runner, input_guardrail, GuardrailFunctionOutput, output_guardrail
from pydantic import BaseModel, Field

load_dotenv(override=True)

class in_sensitive(BaseModel):
    is_sensitive : bool = Field(description = "Check if the query is sensitive or immoral word or not")
    input : str = Field(description= 'input query')


class op_emojis(BaseModel):
    contains_emoji : bool = Field(description='check if the final report contains any emoji in it')
    report : str 


in_agent = Agent(name='sensitive_agent',
                 instructions='Check if the input query is sensitive. Use your intelligence and'
                 'also check for words like child labour, taboo, dowry, suicides, hacking ways, money laundering,'
                 'human traffiking, etc',
                 model='gpt-4o-mini',
                 output_type=in_sensitive)

out_agent = Agent(name='out_emoji_agent',
                  instructions='Check if the final report contains any emojis in it',
                  output_type=op_emojis,
                  model='gpt-4o-mini')


@input_guardrail
async def guard_sensitive_topics(ctx, agent, query):
    '''Check if the input query contains is sensitive or not'''
    result = await Runner.run(in_agent, query, context=ctx.context)
    is_sensitive_query = result.final_output.is_sensitive
    return GuardrailFunctionOutput(output_info=[{'content' : result.final_output}], tripwire_triggered=is_sensitive_query)


@output_guardrail
async def guard_report_emojis(ctx, agent, report):

    raw_text = report.markdownReport if hasattr(report, 'markdownReport') else str(report)
    # Pass the clean string to the checking agent
    result = await Runner.run(out_agent, raw_text)
  
    has_emoji = result.final_output.contains_emoji
    return GuardrailFunctionOutput([{'content' : result.final_output}], tripwire_triggered=has_emoji)
