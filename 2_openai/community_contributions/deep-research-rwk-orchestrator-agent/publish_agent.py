from typing import Dict
# import sendgrid
# from sendgrid.helpers.mail import Email, Mail, Content, To
from pydantic import BaseModel, Field
from agents import Agent, function_tool
import parameters as param

'''
@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("ed@edwarddonner.com")  # put your verified sender here
    to_email = To("ed.donner@gmail.com")  # put your recipient here
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"
'''

@function_tool
def publish_report(report_file_name: str, report_with_title_html: str) -> Dict[str, str]:
    """Publish a report with titleas html"""
    print(f"\n\nPublish report {report_file_name}")
    param.OUTPUT_FILE_ADDRESS.mkdir(parents=True, exist_ok=True)
    output_file_address = param.OUTPUT_FILE_ADDRESS / report_file_name
    with open(output_file_address, "w", encoding="utf-8") as f:
        f.write(report_with_title_html)
    print(f'\nsaved report to file {report_file_name}')
    return report_file_name

class PublishData(BaseModel):
    query: str = Field(description="The query that was used to produce the report")
    report_file_name: str = Field(description="The name of the report file")


publish_agent = Agent[PublishData](
    name="PublishAgent",
    instructions= param.INSTRUCTIONS_PUBLISH,
    tools=[publish_report],
    model= param.MODEL_PUBLISH,
    output_type=PublishData,
)
