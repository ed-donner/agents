import os
from dotenv import load_dotenv
from fastapi  import FastAPI, Request
import uvicorn
from sdr_response_agent import Sdr_Response_Agent

app = FastAPI()

load_dotenv(override=True)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
   

@app.get("/")
def get_app(request: Request):
    # SendGrid sends data as multipart/form-data
    return {"fastapi": "Server up !!"}

@app.post("/")
async def sendgrid_inbound_parse(request: Request):
    # SendGrid sends data as multipart/form-data
      # Verify the security token
    
    form = await request.form()
    envelope = form.get('envelope')  # Contains JSON with "to" and "from"
    sender = form.get('from')        # Sender's email address
    recipient = form.get('to')        # Recipient's email address
    subject = form.get('subject')    # Email subject line
    headers = form.get('headers')
    
    # SendGrid provides both plain text and HTML versions of the reply
    text_body = form.get('text')    # Plain text content
    html_body = form.get('html')    # HTML content

    # Process the data (Log it, save to DB, or trigger an alert)
    print(f"New Reply From: {sender}")
    print(f"Recipient: {recipient}")
    print(f"Subject: {subject}")
    print(f"Headers: {headers}")
    
    final_body = text_body if text_body else html_body
    print(f"Message Body:\n{final_body}")

    sdr_agent = Sdr_Response_Agent(
        agent_email=recipient,
        client_email=sender,
        customer_response=final_body
    )
    await sdr_agent.respond_to_customer()

    # You can extract custom tracking IDs from the "to" or "envelope" fields
    print(f"Envelope Details: {envelope}")

    # Always return a 200 OK status code so SendGrid knows you received it
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",      # Use the "module:instance" string format
        host="127.0.0.1", # Localhost
        port=5000,       # Default FastAPI port
        reload=True      # Auto-reloads server when code changes
)