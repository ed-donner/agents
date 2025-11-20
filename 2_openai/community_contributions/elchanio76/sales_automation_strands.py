import os
import asyncio
import pandas as pd
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models.ollama import OllamaModel
from strands.models.openai import OpenAIModel
from strands.models.anthropic import AnthropicModel

from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

load_dotenv(override=True)

# Load product information
with open('ComplAI_brochure.md', 'r') as file:
    brochure_text = file.read()

@tool
def send_html_email(recipient_email: str, subject: str, html_body: str) -> Dict[str, str]:
    """Send HTML email to recipient"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("lchanio@echyperion.com")  # Update with your verified sender
    to_email = To(recipient_email)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    sg.client.mail.send.post(request_body=mail)
    return {"status": "success"}

class SalesAutomation:
    def __init__(self):
        self.setup_agents()
    
    def setup_agents(self):
        self.picker_model = OpenAIModel(
            client_args = {
                "api_key": os.environ.get('OPENAI_API_KEY')
            },
            # Model config
            model_id = 'gpt-5-mini',
        )
        self.composer_model = AnthropicModel(
            client_args = {
                "api_key": os.environ.get('ANTHROPIC_API_KEY')
            },
            # Model config
            max_tokens = 1028, # Mandatory parameter for Anthropic
            model_id = 'claude-sonnet-4-20250514',
            params = {
                "temperature": 0.8
            }
        )
        self.model = OllamaModel(
            host = 'http://localhost:11434',
            model_id = 'llama3.1:8b',
            temperature = 0.8
        )
        # Customer picker agent
        self.customer_picker = Agent(
            name="Customer Picker",
            callback_handler = None,
            system_prompt=f"""You examine potential recipients and decide if they're a good fit for ComplAI's SOC 2 compliance tool.
            Respond only with YES or NO. Product context: {brochure_text}""",
            model=self.picker_model
        )
        
        # Sales agents
        sales_instructions = [
            f"You are a Professional sales agent for ComplAI SOC 2 compliance tool. Write serious, professional emails.Respond only with the e-mail, without any preamble or explanation. {brochure_text}",
            f"You are an Engaging sales agent for ComplAI SOC 2 compliance tool. Write witty, engaging emails likely to get responses. Respond only with the e-mail, without any preamble or explanation. {brochure_text}",
            f"You are a Concise sales agent for ComplAI SOC 2 compliance tool. Write brief, to-the-point emails. Respond only with the e-mail, without any preamble or explanation. {brochure_text}"
        ]
        
        self.sales_agents = [
            Agent(name=f"Sales Agent {i+1}", system_prompt=instr, model=self.composer_model, callback_handler = None)
            for i, instr in enumerate(sales_instructions)
        ]
        
        # Sales picker agent
        self.sales_picker = Agent(
            name="Sales Picker",
            system_prompt="Pick the best email from options. Reply with the email number only (1, 2, or 3).",
            model=self.picker_model,
            callback_handler = None
        )
        
        # HTML formatter agent
        self.formatter = Agent(
            name="Email Formatter",
            system_prompt="Convert text emails to HTML with professional branding and layout.",
            model=self.model,
            callback_handler = None,
            tools=[send_html_email]
        )
    
    async def filter_customers(self, contacts_df):
        """Filter customers based on relevance"""
        filtered_contacts = []
        
        for _, contact in contacts_df.iterrows():
            message = f"Is {contact['Name']} - {contact['Title']} a good fit for ComplAI's SOC 2 compliance tool?"
            result = await self.customer_picker.invoke_async(message)
    
            if str(result).strip().upper() == "YES":
                filtered_contacts.append(contact)
        
        return pd.DataFrame(filtered_contacts)
    
    async def generate_emails(self, contact):
        """Generate emails from all sales agents"""
        contact_name, contact_title = contact['Name'], contact['Title']
        prompt = f"Write a cold sales email to {contact_name}, who is a {contact_title}. Personalize for their role."
        
        tasks = [agent.invoke_async(prompt) for agent in self.sales_agents]
        results = await asyncio.gather(*tasks)
        
        return [str(result) for result in results]
    
    async def select_best_email(self, emails):
        """Select best email from options"""
        email_options = "\n\n".join([f"Email {i+1}:\n{email}" for i, email in enumerate(emails)])
        result = await self.sales_picker.invoke_async(f"Choose the best email:\n{email_options}")
        
        try:
            choice = int(str(result).strip()) - 1
            return emails[choice]
        except:
            return emails[0]  # Default to first if parsing fails
    
    async def format_and_send(self, email_content, recipient_email):
        """Format email as HTML and send"""
        prompt = f"Convert this email to HTML with professional branding and send to {recipient_email}:\n{email_content}"
        await self.formatter.invoke_async(prompt)
    
    async def run_campaign(self, contacts_file):
        """Run complete sales campaign"""
        # Load contacts
        contacts = pd.read_csv(contacts_file)
        
        # Filter relevant customers
        print("Filtering customers...")
        relevant_contacts = await self.filter_customers(contacts)
        print(f"Selected {len(relevant_contacts)} relevant contacts")
        
        # Process each contact
        for _, contact in relevant_contacts.iterrows():
            print(f"Processing {contact['Name']}...")
            
            # Generate multiple email options
            emails = await self.generate_emails(contact)
            
            # Select best email
            best_email = await self.select_best_email(emails)
            
            # Format and send
            await self.format_and_send(best_email, contact['Email'])
            
            print(f"Email sent to {contact['Name']}")

async def main():
    automation = SalesAutomation()
    await automation.run_campaign('contact_list.csv')

if __name__ == "__main__":
    asyncio.run(main())
