from pydantic import BaseModel
from agents import Agent

class PiiCheckOutput(BaseModel):
  pii_is_in_message: bool

class PIIGuardrailAgent:
    def __init__(self):
        self.agent = Agent(
            name = "PII Guardrail Agent",
            instructions = (
              "You are a vigilant PII (Personally Identifiable Information) guardrail agent."
              "Your role is to meticulously analyze incoming messages for any presence of PII data."
              "If you detect any PII data in the message, you MUST respond with a structured output "
              "indicating that PII was found, along with the specific types of PII detected."
              "If no PII data is found, respond indicating that the message is clean."
              
              "The types of PII data you should look for include, but are not limited to: "  
              "- credit card number"
              "- bank account number"
              "- date of birth"
              "- driver's license number"
              "- email address"
              "- home address"
              "- passport number"
              "- phone number"
              "- social security number"
              "- ssn"
              "- persons names"
            ),
            output_type=PiiCheckOutput,
            model = "gpt-4o-mini",            
        ) 
