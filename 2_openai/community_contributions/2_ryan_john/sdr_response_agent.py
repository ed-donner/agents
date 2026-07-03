from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, trace 

load_dotenv()



@function_tool
def send_email(body: str, sender_email:str, recipent_email:str):
    import os
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content

    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    """ Send out an email with the given body to all sales prospects """
    sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
    from_email = Email(sender_email)  # Change to your verified sender
    to_email = To(recipent_email)  # Change to your recipient
    content = Content("text/plain", body)
    mail = Mail(from_email, to_email, "Sales email", content).get()
    response = sg.client.mail.send.post(request_body=mail)

    return {"status": "success", "message": f"Email sent successfully to {recipent_email}",
            "status_code": response.status_code}

class Sdr_Response_Agent:

    def __init__(self, agent_email, client_email, customer_response):
        self.agent_email =  agent_email
        self.client_email = client_email
        self.customer_response = customer_response
        
        self.instruction_1 = f"""You are a sales agent working for ComplAI,
                    a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI.
                    Whenever a customer replies to an email, you will have to act and based off the reply, 
                    based of the message body sent, you will have to analyze the customer query and craft the appropriate response 
                    in a professional yet engaging tone. In order to do this, you have access to the send_email tool.
                    Please ensure that you pass the correct email addresses to the tool:
                    - sender_email: {self.agent_email}
                    - recipent_email: {self.client_email}"""
                    
        self.agent = Agent(
            name="Customer Relationship Agent",
            instructions=self.instruction_1,
            model="gpt-4o-mini",
            tools=[send_email]
        )
        
    async def respond_to_customer(self):
        message = (
            f"The customer (email: {self.client_email}) sent the following response:\n"
            f"\"\"\"\n{self.customer_response}\n\"\"\"\n\n"
            f"Please analyze this customer query, craft an appropriate professional response, "
            f"and send an email using the send_email tool. "
            f"Ensure sender_email is {self.agent_email} and recipent_email is {self.client_email}."
        )
        with trace("Customer Relationship DR"):
            result = await Runner.run(self.agent, message)
