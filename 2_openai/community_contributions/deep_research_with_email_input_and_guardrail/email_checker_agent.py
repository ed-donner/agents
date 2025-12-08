
from agents import Agent, input_guardrail, GuardrailFunctionOutput
from dotenv import load_dotenv
import os
import requests


load_dotenv(override=True)
kickbox_api_key = os.getenv('KICKBOX_API_KEY')

async def check_email_kickbox(email) -> dict[str, str]:
    verify_url = f'https://api.kickbox.com/v2/verify?email={email}&apikey={kickbox_api_key}'
    try:
        response = requests.get(verify_url)

        if response.status_code == 200:
            data = response.json()
            if data and data.get('success'): 
                return {'status': data.get('result'), 'reason': data.get('reason')}
            else:    
                return {'status': 'unverifiable', 'reason': 'unexpected result from email verification server'}
        else:
            return {'status': 'unverifiable', 'reason': f'received http response code: {response.status_code} from email verification server'}

    except Exception as e:
        return {'status': 'unverifiable', 'reason': 'unexpected exception from email verification server'}


@input_guardrail
async def guardrail_against_email(ctx, agent, email):
    result = await check_email_kickbox(email)
    return GuardrailFunctionOutput(output_info=result, tripwire_triggered=(result['status'] != 'deliverable'))

email_checker_agent = Agent(
    name="Email Checker",
    instructions="Verify email_to with guardrail_against_email",
    model="gpt-4o-mini",
    input_guardrails=[guardrail_against_email]
)    