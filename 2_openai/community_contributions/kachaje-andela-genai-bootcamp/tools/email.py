import os
from typing import Dict
import time
import re
import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, To
from agents import function_tool
from utils.globals import span


def _html_to_plain_text(html: str) -> str:
    """Convert HTML content to plain text by stripping tags and decoding entities."""
    # Remove script and style elements and their content
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Replace common HTML entities
    html = html.replace('&nbsp;', ' ')
    html = html.replace('&amp;', '&')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    html = html.replace('&quot;', '"')
    html = html.replace('&#39;', "'")
    
    # Replace block elements with line breaks
    html = re.sub(r'</(p|div|h[1-6]|li|tr|br)[^>]*>', '\n', html, flags=re.IGNORECASE)
    
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
    text = text.strip()
    
    return text


def _send_email_impl(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body using SendGrid API.
    
    Includes retry logic for transient failures and better error handling.
    Creates both HTML and plain text versions for better email client compatibility.
    """
    api_key = os.environ.get("SENDGRID_API_KEY")

    if not api_key:
        error_msg = "SENDGRID_API_KEY environment variable is not set"
        print(f"ERROR: {error_msg}")
        return {"status": "error", "message": error_msg}

    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            with span("send_email", "Sending email"):
                if attempt > 0:
                    print(f"Retry attempt {attempt + 1}/{max_retries}...")
                    time.sleep(retry_delay * attempt)  # Exponential backoff
                
                print(f"-> Tool called: send_email(subject={subject}, html_body={html_body[:100]}...)")
                sg = sendgrid.SendGridAPIClient(api_key=api_key)
                from_email = Email("chimwemwe.kachaje@andela.com")
                to_email = To("chimwemwe.kachaje@andela.com")
                
                # Create both HTML and plain text versions for better email client compatibility
                html_content = Content("text/html", html_body)
                plain_text_body = _html_to_plain_text(html_body)
                plain_text_content = Content("text/plain", plain_text_body)
                
                # Create Mail object with both content types
                mail = Mail(from_email, to_email, subject, html_content)
                mail.add_content(plain_text_content)
                mail = mail.get()
                
                # Make the API call with timeout
                response = sg.client.mail.send.post(request_body=mail)

                print(f"SendGrid response status code: {response.status_code}")

                # Check if email was sent successfully (202 is success)
                if response.status_code == 202:
                    print("Email sent successfully!")
                    return {"status": "success", "message": "Email sent successfully"}
                elif response.status_code == 429:
                    # Rate limit error - retry with longer delay
                    error_msg = "Rate limit exceeded. Will retry..."
                    print(f"WARNING: {error_msg}")
                    if attempt < max_retries - 1:
                        retry_delay = 5  # Longer delay for rate limits
                        continue
                else:
                    # Try to get error details from response body
                    error_body = (
                        response.body.decode("utf-8") if response.body else "Unknown error"
                    )
                    error_msg = f"Failed to send email. Status: {response.status_code}, Error: {error_body}"
                    print(f"ERROR: {error_msg}")
                    # Don't retry for client errors (4xx except 429)
                    if 400 <= response.status_code < 500 and response.status_code != 429:
                        return {"status": "error", "message": error_msg}
                    # Retry for server errors (5xx) or other errors
                    if attempt < max_retries - 1:
                        continue
                    return {"status": "error", "message": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            print(f"ERROR: {error_msg}")
            # Retry on network/connection errors
            if attempt < max_retries - 1 and (
                "timeout" in str(e).lower() or 
                "connection" in str(e).lower() or
                "network" in str(e).lower()
            ):
                print(f"Network error detected, will retry...")
                continue
            return {"status": "error", "message": error_msg}
    
    # If we get here, all retries failed
    return {"status": "error", "message": f"Failed to send email after {max_retries} attempts"}


# Create the tool for use with agents
send_email = function_tool(_send_email_impl)
