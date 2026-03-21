
from brevo import AsyncBrevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)
from langchain.tools import tool, BaseTool
import os

class EmailSender:
    def __init__(self, api_key) -> None:
        self.client = AsyncBrevo(
            api_key=api_key,
        )

    async def send_email_full(self, frm, to, subject, body):
        '''frm, to - are tuples: (name, emailId)'''
        await self.client.transactional_emails.send_transac_email(
            to=[SendTransacEmailRequestToItem(
                email=to[1],
                name=to[0]
            )],
            sender=SendTransacEmailRequestSender(
                email=frm[1],
                name=frm[0],
            ),
            subject=subject,
            html_content=body
        )
        return "success"


@tool
async def send_email(subject:str, body:str) -> str:
    '''send email using subject and HTML body; From and To are taken care of'''
    brevo_key = os.getenv("BREVO_API_KEY")
    sender = EmailSender(brevo_key)
    try:
        await sender.send_email_full(
            frm = ("Raju D","xxxx@domain.com"), 
            to = ("Raju","xyz@domain.com"),
            subject = subject,
            body = body
            )
    except Exception as e:
        print(str(e))
    finally:
        return "success"
