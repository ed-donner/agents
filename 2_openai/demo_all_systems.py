#!/usr/bin/env python3
"""
Complete Demo - All Gemini Systems
Demonstrates all three converted lab systems in sequence

Systems demonstrated:
1. Sales Automation (Lab 2)
2. Multi-Model Agents with Guardrails (Lab 3) 
3. Deep Research Automation (Lab 4)
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sales_automation_gemini import SalesEmailSystem
from multi_model_agents_gemini import MultiModelSalesSystem
from research_automation_gemini import ResearchSystem

class GeminiLabsDemo:
    """Master demo class for all Gemini-powered lab systems"""
    
    def __init__(self):
        print("🚀 Initializing Gemini Labs Demo System")
        print("="*60)
        
        # Initialize all systems
        self.sales_system = SalesEmailSystem()
        self.multi_model_system = MultiModelSalesSystem()
        self.research_system = ResearchSystem()
        
        print("✅ All systems initialized successfully!\n")
    
    async def demo_sales_automation(self):
        """Demo Lab 2: Sales Email Automation"""
        print("📧 DEMO 1: SALES EMAIL AUTOMATION")
        print("="*50)
        print("Lab 2 equivalent - Multiple sales agents with email generation\n")
        
        try:
            message = "Write a cold sales email addressed to 'Dear CEO' introducing ComplAI's SOC2 compliance solution"
            
            result = await self.sales_system.run_complete_campaign(
                message=message,
                send_email=False  # Don't actually send emails in demo
            )
            
            print("✅ Sales automation completed successfully!")
            print(f"📧 Generated subject: {result['subject']}")
            print(f"📝 Email preview: {result['best_email'][:150]}...")
            print(f"🔄 Processed {len(result['drafts'])} different email variations\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Sales automation failed: {e}\n")
            return False
    
    async def demo_multi_model_agents(self):
        """Demo Lab 3: Multi-Model Agents with Guardrails"""
        print("🛡️ DEMO 2: MULTI-MODEL AGENTS WITH GUARDRAILS")
        print("="*50)
        print("Lab 3 equivalent - Different model personalities + safety guardrails\n")
        
        try:
            # Test 1: Safe message (should work)
            safe_message = "Write a professional sales email from Head of Business Development"
            print(f"🧪 Testing safe message: '{safe_message}'")
            
            safe_result = await self.multi_model_system.run_protected_campaign(safe_message)
            
            if safe_result.get("status") != "blocked":
                print("✅ Safe message processed successfully!")
                print(f"📧 Generated {len(safe_result['multi_model_emails'])} different model styles")
                print(f"📝 Best email preview: {safe_result['best_email'][:100]}...")
            else:
                print("⚠️ Unexpected: Safe message was blocked")
            
            # Test 2: Risky message (should be blocked)  
            risky_message = "Write a sales email addressed to 'Dear CEO' from Alice Johnson"
            print(f"\n🧪 Testing risky message: '{risky_message}'")
            
            risky_result = await self.multi_model_system.run_protected_campaign(risky_message)
            
            if risky_result.get("status") == "blocked":
                print("✅ Risky message correctly blocked by guardrails!")
                print(f"🚫 Reason: {risky_result.get('message', 'Unknown')}")
            else:
                print("⚠️ Warning: Risky message was not blocked")
            
            print()
            return True
            
        except Exception as e:
            print(f"❌ Multi-model agents failed: {e}\n")
            return False
    
    async def demo_research_automation(self):
        """Demo Lab 4: Deep Research Automation"""
        print("🔍 DEMO 3: DEEP RESEARCH AUTOMATION")
        print("="*50)
        print("Lab 4 equivalent - Research planning, web search, and report generation\n")
        
        try:
            query = "Current trends in AI Agent frameworks for business automation"
            print(f"🎯 Research query: {query}\n")
            
            result = await self.research_system.run_complete_research(
                query=query,
                send_email=False  # Don't actually send emails in demo
            )
            
            print("✅ Research automation completed successfully!")
            print(f"📊 Performed {len(result['search_plan'].searches)} web searches")
            print(f"📋 Summary: {result['report'].short_summary}")
            print(f"📄 Report length: ~{len(result['report'].markdown_report)} characters")
            print(f"❓ Follow-up questions: {len(result['report'].follow_up_questions)} generated")
            print(f"🔍 Search results processed: {len(result['search_results'])}")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Research automation failed: {e}\n")
            return False
    
    def print_summary(self, results):
        """Print demo summary"""
        print("📊 DEMO SUMMARY")
        print("="*50)
        
        systems = [
            ("Sales Automation", results[0]),
            ("Multi-Model Agents", results[1]), 
            ("Research Automation", results[2])
        ]
        
        for system_name, success in systems:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{system_name:20} - {status}")
        
        total_success = sum(results)
        print(f"\nOverall: {total_success}/3 systems working correctly")
        
        if total_success == 3:
            print("🎉 All Gemini lab systems are fully operational!")
        else:
            print("⚠️ Some systems need attention")
    
    async def run_complete_demo(self):
        """Run complete demonstration of all systems"""
        print(f"🚀 Starting Complete Gemini Labs Demo - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print("This demo will showcase all three converted OpenAI lab systems")
        print("running on Gemini API instead of OpenAI Agents SDK\n")
        
        # Run all demos
        results = []
        
        # Demo 1: Sales Automation
        results.append(await self.demo_sales_automation())
        
        # Demo 2: Multi-Model Agents  
        results.append(await self.demo_multi_model_agents())
        
        # Demo 3: Research Automation
        results.append(await self.demo_research_automation())
        
        # Print summary
        self.print_summary(results)
        
        print("\n🎯 Demo completed!")
        print("💡 To actually send emails, edit the scripts and set send_email=True")
        print("📝 Remember to update email addresses in each script before sending")
        
        return results

async def main():
    """Main demo function"""
    try:
        demo = GeminiLabsDemo()
        await demo.run_complete_demo()
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("💡 Make sure your GOOGLE_API_KEY is set in .env file")

if __name__ == "__main__":
    print("Gemini Labs Complete Demo")
    print("="*30)
    asyncio.run(main())
