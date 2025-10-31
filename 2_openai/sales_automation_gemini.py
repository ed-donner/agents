#!/usr/bin/env python3
"""
Sales Email Automation - Gemini Version
Replicated from OpenAI Agents SDK to work with Gemini API

Features:
- Multiple sales agents with different personalities
- Parallel execution
- Best email selection
- HTML conversion
- Email sending via SendGrid
"""

from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import asyncio
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import Dict, List
import time

load_dotenv(override=True)

# Setup Gemini client
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class GeminiAgent:
    """Simple agent class to replicate OpenAI Agents SDK functionality"""
    
    def __init__(self, name: str, instructions: str, tools: list = None):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []
        self.client = gemini
    
    def run(self, message: str) -> str:
        """Run the agent with a message"""
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": message}
        ]
        
        response = self.client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=messages
        )
        
        return response.choices[0].message.content

class SalesEmailSystem:
    """Complete sales email automation system"""
    
    def __init__(self):
        # Agent instructions
        self.instructions = {
            'professional': "You are a sales agent working for ComplAI, a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. You write professional, serious cold emails.",
            
            'engaging': "You are a humorous, engaging sales agent working for ComplAI, a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. You write witty, engaging cold emails that are likely to get a response.",
            
            'concise': "You are a busy sales agent working for ComplAI, a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. You write concise, to the point cold emails.",
            
            'picker': "You pick the best cold sales email from the given options. Imagine you are a customer and pick the one you are most likely to respond to. Do not give an explanation; reply with the selected email only.",
            
            'subject_writer': "You can write a subject for a cold sales email. You are given a message and you need to write a subject for an email that is likely to get a response. Reply with only the subject line.",
            
            'html_converter': "You can convert a text email body to an HTML email body. You are given a text email body which might have some markdown and you need to convert it to an HTML email body with simple, clear, compelling layout and design."
        }
        
        # Create agents
        self.sales_agents = [
            GeminiAgent("Professional Sales Agent", self.instructions['professional']),
            GeminiAgent("Engaging Sales Agent", self.instructions['engaging']),
            GeminiAgent("Concise Sales Agent", self.instructions['concise'])
        ]
        
        self.picker = GeminiAgent("Sales Picker", self.instructions['picker'])
        self.subject_writer = GeminiAgent("Subject Writer", self.instructions['subject_writer'])
        self.html_converter = GeminiAgent("HTML Converter", self.instructions['html_converter'])
    
    async def run_agent_async(self, agent, message):
        """Async wrapper for agent execution"""
        return agent.run(message)
    
    async def generate_emails_parallel(self, message: str):
        """Generate multiple email drafts in parallel"""
        print("📝 Generating email drafts from multiple agents...")
        tasks = [self.run_agent_async(agent, message) for agent in self.sales_agents]
        results = await asyncio.gather(*tasks)
        return results
    
    def select_best_email(self, drafts: List[str]) -> str:
        """Select the best email from multiple drafts"""
        print("🎯 Selecting best email...")
        emails_text = "Cold sales emails:\n\n" + "\n\nEmail:\n\n".join(drafts)
        return self.picker.run(emails_text)
    
    def generate_subject(self, email_body: str) -> str:
        """Generate subject line for the email"""
        print("📧 Creating subject line...")
        return self.subject_writer.run(email_body)
    
    def convert_to_html(self, email_body: str) -> str:
        """Convert email to HTML format"""
        print("🎨 Converting to HTML...")
        return self.html_converter.run(email_body)
    
    def send_email(self, subject: str, html_body: str, from_email: str, to_email: str) -> Dict[str, str]:
        """Send email via SendGrid"""
        try:
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            from_email_obj = Email(from_email)
            to_email_obj = To(to_email)
            content = Content("text/html", html_body)
            mail = Mail(from_email_obj, to_email_obj, subject, content).get()
            response = sg.client.mail.send.post(request_body=mail)
            
            if response.status_code == 202:
                return {"status": "success", "message": "Email sent successfully"}
            else:
                return {"status": "failed", "message": f"SendGrid returned {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def run_complete_campaign(self, message: str, from_email: str = None, to_email: str = None, send_email: bool = False):
        """Run complete sales email campaign"""
        print("🚀 Starting sales email campaign...\n")
        
        # Step 1: Generate drafts in parallel
        drafts = await self.generate_emails_parallel(message)
        
        print(f"Generated {len(drafts)} email drafts\n")
        
        # Step 2: Select best email
        best_email = self.select_best_email(drafts)
        
        # Step 3: Generate subject
        subject = self.generate_subject(best_email)
        
        # Step 4: Convert to HTML
        html_body = self.convert_to_html(best_email)
        
        # Step 5: Send email if requested
        email_result = None
        if send_email and from_email and to_email:
            print("📤 Sending email...")
            email_result = self.send_email(subject, html_body, from_email, to_email)
            print(f"Email status: {email_result['status']}")
        
        return {
            "drafts": drafts,
            "best_email": best_email,
            "subject": subject,
            "html_body": html_body,
            "email_result": email_result
        }

async def main():
    """Main function to demonstrate the system"""
    
    # Create sales system
    sales_system = SalesEmailSystem()
    
    # Test message
    message = "Write a cold sales email addressed to 'Dear CEO' from Alice at ComplAI"
    
    # Run campaign (without sending actual email)
    result = await sales_system.run_complete_campaign(
        message=message,
        from_email="YOUR_VERIFIED_EMAIL@example.com",  # Change this
        to_email="YOUR_EMAIL@example.com",             # Change this
        send_email=False  # Set to True to actually send email
    )
    
    print("\n" + "="*60)
    print("📧 CAMPAIGN RESULTS")
    print("="*60)
    print(f"📧 Subject: {result['subject']}")
    print(f"\n📝 Best Email:\n{result['best_email']}")
    print(f"\n🎨 HTML Preview:\n{result['html_body'][:300]}...")
    
    if result['email_result']:
        print(f"\n📤 Email Status: {result['email_result']['status']}")

if __name__ == "__main__":
    print("Sales Email Automation - Gemini Version")
    print("="*50)
    asyncio.run(main())
