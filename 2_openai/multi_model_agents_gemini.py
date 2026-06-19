#!/usr/bin/env python3
"""
Multi-Model Agents - Gemini Version
Demonstrates using different AI models with guardrails and structured outputs

Features:
- Gemini as primary model (simulating different model personalities)
- Structured outputs using Pydantic
- Input/output guardrails
- Sales email workflow with protection
"""

from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import asyncio
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import Dict, List
from pydantic import BaseModel, Field
import re

load_dotenv(override=True)

# Setup Gemini client  
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class NameCheckOutput(BaseModel):
    """Structure for name detection guardrail"""
    is_name_in_message: bool = Field(description="Whether a personal name was detected in the message")
    name: str = Field(description="The detected name, if any")

class EmailOutput(BaseModel):
    """Structure for email generation"""
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    tone: str = Field(description="Detected tone (professional, engaging, concise)")

class GeminiAgent:
    """Advanced agent class with structured outputs and guardrails"""
    
    def __init__(self, name: str, instructions: str, output_type=None, input_guardrails=None):
        self.name = name
        self.instructions = instructions
        self.output_type = output_type
        self.input_guardrails = input_guardrails or []
        self.client = gemini
    
    def run(self, message: str):
        """Run the agent with guardrails and structured output"""
        
        # Apply input guardrails
        for guardrail in self.input_guardrails:
            guardrail_result = guardrail(message)
            if guardrail_result.get('tripwire_triggered'):
                return f"❌ Guardrail triggered: {guardrail_result.get('reason', 'Unknown')}"
        
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": message}
        ]
        
        if self.output_type:
            # For structured output
            enhanced_instructions = self.instructions + f"\n\nPlease respond with a valid JSON object matching this structure: {self.output_type.model_json_schema()}"
            messages[0]["content"] = enhanced_instructions
            
            response = self.client.chat.completions.create(
                model="gemini-1.5-flash",
                messages=messages
            )
            
            content = response.choices[0].message.content
            
            try:
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    parsed_data = json.loads(json_str)
                    return self.output_type(**parsed_data)
                else:
                    return self._create_fallback_response(content)
            except Exception as e:
                print(f"Warning: Could not parse structured output: {e}")
                return self._create_fallback_response(content)
        else:
            response = self.client.chat.completions.create(
                model="gemini-1.5-flash",
                messages=messages
            )
            return response.choices[0].message.content
    
    def _create_fallback_response(self, content: str):
        """Create fallback response for structured output"""
        if self.output_type == NameCheckOutput:
            # Simple name detection
            common_names = ['alice', 'bob', 'charlie', 'david', 'eve', 'frank', 'grace']
            detected_name = None
            is_name_found = False
            
            for name in common_names:
                if name.lower() in content.lower():
                    detected_name = name
                    is_name_found = True
                    break
            
            return NameCheckOutput(
                is_name_in_message=is_name_found,
                name=detected_name or "No name detected"
            )
        elif self.output_type == EmailOutput:
            return EmailOutput(
                subject="Generated Email",
                body=content,
                tone="unknown"
            )
        return content

class GuardrailSystem:
    """System for managing input and output guardrails"""
    
    def __init__(self):
        self.name_checker = GeminiAgent(
            name="Name Checker",
            instructions="Check if the user is including someone's personal name in what they want you to do. Look for common personal names.",
            output_type=NameCheckOutput
        )
    
    def check_for_names(self, message: str) -> Dict:
        """Input guardrail to check for personal names"""
        result = self.name_checker.run(message)
        return {
            'tripwire_triggered': result.is_name_in_message,
            'reason': f"Personal name detected: {result.name}" if result.is_name_in_message else None,
            'details': result
        }

class MultiModelSalesSystem:
    """Sales system with multiple model personalities and guardrails"""
    
    def __init__(self):
        self.guardrail_system = GuardrailSystem()
        
        # Create different "models" (really different personalities of Gemini)
        self.deepseek_agent = GeminiAgent(
            name="DeepSeek-style Agent",
            instructions="""You are a sales agent working for ComplAI, channeling the analytical style of DeepSeek models.
You provide logical, well-structured cold emails with clear value propositions. 
Company: ComplAI - SaaS tool for SOC2 compliance and audit preparation, powered by AI.
Write professional, analytical cold emails.""",
            output_type=EmailOutput
        )
        
        self.gemini_agent = GeminiAgent(
            name="Gemini-style Agent", 
            instructions="""You are a sales agent working for ComplAI, using Gemini's creative and engaging style.
You write innovative, personalized cold emails that stand out.
Company: ComplAI - SaaS tool for SOC2 compliance and audit preparation, powered by AI.
Write creative, engaging cold emails that are likely to get responses.""",
            output_type=EmailOutput
        )
        
        self.llama_agent = GeminiAgent(
            name="Llama-style Agent",
            instructions="""You are a sales agent working for ComplAI, emulating Llama's concise and direct style.
You write brief, to-the-point cold emails that respect busy executives' time.
Company: ComplAI - SaaS tool for SOC2 compliance and audit preparation, powered by AI.
Write concise, direct cold emails.""",
            output_type=EmailOutput
        )
        
        # Protected agent with guardrails
        self.protected_agent = GeminiAgent(
            name="Protected Sales Manager",
            instructions="""You are a careful sales manager at ComplAI. You generate sales emails but refuse 
to include specific personal names in emails for privacy protection. If a personal name is detected, 
decline the request and suggest using a title instead.""",
            input_guardrails=[self.guardrail_system.check_for_names]
        )
        
        self.picker = GeminiAgent(
            name="Email Picker",
            instructions="Pick the best cold sales email from given options. Select the one most likely to get a response from a CEO. Reply only with the selected email content."
        )
    
    async def generate_multi_model_emails(self, message: str):
        """Generate emails using different model personalities"""
        print("🤖 Generating emails with different AI personalities...")
        
        agents = [self.deepseek_agent, self.gemini_agent, self.llama_agent]
        
        tasks = [asyncio.create_task(self._run_agent_async(agent, message)) for agent in agents]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def _run_agent_async(self, agent, message):
        """Async wrapper for agent execution"""
        return agent.run(message)
    
    def select_best_email(self, emails: List[EmailOutput]) -> str:
        """Select best email from multiple options"""
        print("🎯 Selecting best email...")
        
        email_options = "\n\n---EMAIL OPTION---\n\n".join([
            f"Subject: {email.subject}\nBody: {email.body}" for email in emails
        ])
        
        return self.picker.run(f"Select the best email from these options:\n\n{email_options}")
    
    def send_email(self, subject: str, body: str, from_email: str, to_email: str) -> Dict[str, str]:
        """Send email via SendGrid"""
        try:
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            from_email_obj = Email(from_email)
            to_email_obj = To(to_email)
            content = Content("text/html", body)
            mail = Mail(from_email_obj, to_email_obj, subject, content).get()
            response = sg.client.mail.send.post(request_body=mail)
            
            if response.status_code == 202:
                return {"status": "success", "message": "Email sent successfully"}
            else:
                return {"status": "failed", "message": f"SendGrid returned {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def run_protected_campaign(self, message: str):
        """Run campaign with guardrails protection"""
        print("🛡️ Running protected sales campaign...")
        
        # Try to run with protected agent
        result = self.protected_agent.run(message)
        
        if isinstance(result, str) and "❌ Guardrail triggered" in result:
            print(f"🚫 Campaign blocked: {result}")
            return {"status": "blocked", "message": result}
        
        # If not blocked, proceed with normal campaign
        return await self.run_complete_campaign(message, send_email=False)
    
    async def run_complete_campaign(self, message: str, from_email: str = None, to_email: str = None, send_email: bool = False):
        """Run complete multi-model sales campaign"""
        print("🚀 Starting multi-model sales campaign...\n")
        
        # Step 1: Generate emails with different personalities
        email_results = await self.generate_multi_model_emails(message)
        
        print(f"Generated {len(email_results)} emails with different model styles\n")
        
        # Step 2: Display all emails
        for i, email in enumerate(email_results, 1):
            agent_names = ["DeepSeek-style", "Gemini-style", "Llama-style"]
            print(f"📧 {agent_names[i-1]} Email:")
            print(f"Subject: {email.subject}")
            print(f"Tone: {email.tone}")
            print(f"Body: {email.body[:100]}...")
            print("-" * 40)
        
        # Step 3: Select best email
        best_email = self.select_best_email(email_results)
        
        # Step 4: Send email if requested
        email_result = None
        if send_email and from_email and to_email:
            print("📤 Sending best email...")
            # Extract subject from best email (simple heuristic)
            lines = best_email.split('\n')
            subject = lines[0] if lines else "Sales Email"
            if subject.startswith("Subject:"):
                subject = subject.replace("Subject:", "").strip()
            
            email_result = self.send_email(subject, best_email, from_email, to_email)
            print(f"Email status: {email_result['status']}")
        
        return {
            "message": message,
            "multi_model_emails": email_results,
            "best_email": best_email,
            "email_result": email_result
        }

async def main():
    """Main function to demonstrate multi-model system"""
    
    # Create multi-model system
    sales_system = MultiModelSalesSystem()
    
    print("=== TESTING GUARDRAILS ===")
    
    # Test 1: Message with personal name (should be blocked)
    blocked_message = "Send a cold sales email addressed to 'Dear CEO' from Alice"
    print(f"\n🧪 Testing protected campaign with: {blocked_message}")
    blocked_result = await sales_system.run_protected_campaign(blocked_message)
    
    # Test 2: Message without personal name (should work)
    safe_message = "Send a cold sales email addressed to 'Dear CEO' from Head of Business Development"
    print(f"\n🧪 Testing protected campaign with: {safe_message}")
    safe_result = await sales_system.run_protected_campaign(safe_message)
    
    print("\n" + "=" * 60)
    print("📊 MULTI-MODEL CAMPAIGN RESULTS")
    print("=" * 60)
    
    if safe_result.get("status") != "blocked":
        print("✅ Campaign completed successfully")
        print(f"\n🎯 Best Email Preview:\n{safe_result['best_email'][:300]}...")
    else:
        print("🚫 Campaign was blocked by guardrails")

if __name__ == "__main__":
    print("Multi-Model Agents with Guardrails - Gemini Version")
    print("="*60)
    asyncio.run(main())
