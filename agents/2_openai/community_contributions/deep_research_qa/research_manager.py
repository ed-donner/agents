from agents import Runner, trace, gen_trace_id, Agent, function_tool
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifier_agent import clarifier_agent, ClarificationData
from evaluator_agent import evaluator_agent, optimizer_agent, EvaluationResult, OptimizedReport
import asyncio
from typing import Dict, Any, AsyncGenerator

# Legacy ResearchManager class for backward compatibility
class ResearchManager:

    async def run_with_clarification(self, query: str):
        """ Run the clarification step and return clarifying questions """
        trace_id = gen_trace_id()
        with trace("Clarification trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            print("Generating clarifying questions...")
            
            result = await Runner.run(
                clarifier_agent,
                f"Query: {query}",
            )
            
            clarification_data = result.final_output_as(ClarificationData)
            print(f"Generated {len(clarification_data.questions)} clarifying questions")
            
            return {
                "questions": clarification_data.questions,
                "trace_id": trace_id
            }

    async def run_research_with_answers(self, query: str, answers: list[str]):
        """ Run the full research process with clarification answers """
        trace_id = gen_trace_id()
        with trace("Research with clarification trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            print("Starting research with clarifications...")
            
            # Use the new manager agent instead
            clarified_query = self._format_clarified_query(query, answers)
            
            result = await Runner.run(
                ResearchManagerAgent,
                f"Research Query: {clarified_query}",
            )
            
            return {
                "report": result.final_output,
                "trace_id": trace_id
            }

    def _format_clarified_query(self, original_query: str, answers: list[str]) -> str:
        """ Format the original query with clarification answers """
        clarifications = []
        for i, answer in enumerate(answers, 1):
            if answer.strip():
                clarifications.append(f"{i}. {answer.strip()}")
        
        if clarifications:
            clarified_query = f"""Original query: {original_query}

Clarifications provided:
{chr(10).join(clarifications)}

Please use these clarifications to focus and refine the research approach."""
        else:
            clarified_query = original_query
            
        return clarified_query

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            
            # Use the new manager agent
            result = await Runner.run(ResearchManagerAgent, f"Research Query: {query}")
            yield "Research complete"
            yield result.final_output

# Function tools for the manager agent to orchestrate the research process
@function_tool
async def plan_research(query: str) -> Dict[str, Any]:
    """ Plan the research searches for a given query """
    print("Planning searches...")
    result = await Runner.run(planner_agent, f"Query: {query}")
    search_plan = result.final_output_as(WebSearchPlan)
    print(f"Will perform {len(search_plan.searches)} searches")
    return {
        "searches": [{"query": item.query, "reason": item.reason} for item in search_plan.searches],
        "plan_ready": True
    }

@function_tool
async def perform_search(search_query: str, reason: str) -> str:
    """ Perform a single web search and return summarized results """
    print(f"Searching for: {search_query}")
    input_text = f"Search term: {search_query}\nReason for searching: {reason}"
    try:
        result = await Runner.run(search_agent, input_text)
        return str(result.final_output)
    except Exception as e:
        print(f"Search failed for '{search_query}': {e}")
        return f"Search failed for '{search_query}': {str(e)}"

@function_tool
async def write_initial_report(query: str, search_results: str) -> Dict[str, Any]:
    """ Generate an initial research report from search results """
    print("Writing initial report...")
    input_text = f"Original query: {query}\nSummarized search results: {search_results}"
    result = await Runner.run(writer_agent, input_text)
    report_data = result.final_output_as(ReportData)
    print("Initial report completed")
    return {
        "markdown_report": report_data.markdown_report,
        "short_summary": report_data.short_summary,
        "follow_up_questions": report_data.follow_up_questions
    }

@function_tool
async def evaluate_report(query: str, report: str) -> Dict[str, Any]:
    """ Evaluate the quality of a research report """
    print("Evaluating report quality...")
    input_text = f"Original Query: {query}\n\nReport to Evaluate:\n{report}"
    result = await Runner.run(evaluator_agent, input_text)
    evaluation = result.final_output_as(EvaluationResult)
    print(f"Evaluation complete - Score: {evaluation.overall_score}/10, Needs refinement: {evaluation.needs_refinement}")
    return {
        "score": evaluation.overall_score,
        "strengths": evaluation.strengths,
        "weaknesses": evaluation.weaknesses,
        "suggestions": evaluation.suggestions,
        "needs_refinement": evaluation.needs_refinement,
        "refinement_requirements": evaluation.refined_requirements
    }

@function_tool
async def optimize_report(query: str, original_report: str, evaluation_feedback: str) -> str:
    """ Optimize and improve a research report based on evaluation feedback """
    print("Optimizing report...")
    input_text = f"""Original Query: {query}

Original Report:
{original_report}

Evaluation Feedback:
{evaluation_feedback}

Please improve the report based on this feedback."""
    
    result = await Runner.run(optimizer_agent, input_text)
    optimized = result.final_output_as(OptimizedReport)
    print("Report optimization complete")
    return optimized.improved_markdown_report

# Regular function that can be called directly
async def _send_report_email_to_address(report: str, recipient_email: str) -> Dict[str, str]:
    """ Send the final research report via email to a specific address """
    import os
    import sendgrid
    from sendgrid.helpers.mail import Email, Mail, Content, To
    
    print(f"Sending email to: {recipient_email}")
    
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        from_email = Email("mantomarchi300@outlook.com")  # Verified sender
        to_email = To(recipient_email)  # User-provided email
        
        # Create a nice subject line
        subject = "🔍 Your Research Report is Ready"
        
        # Convert markdown to HTML for better email formatting
        import re
        
        # Basic markdown to HTML conversion
        html_report = report
        
        # Convert markdown links to HTML links with styling
        html_report = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color: #2563eb; text-decoration: none; border-bottom: 1px solid #2563eb;" target="_blank">\1</a>', html_report)
        
        # Convert headers
        html_report = re.sub(r'^### (.*$)', r'<h3 style="color: #2563eb; margin-top: 25px; margin-bottom: 10px;">\1</h3>', html_report, flags=re.MULTILINE)
        html_report = re.sub(r'^## (.*$)', r'<h2 style="color: #1d4ed8; margin-top: 30px; margin-bottom: 15px;">\1</h2>', html_report, flags=re.MULTILINE)
        html_report = re.sub(r'^# (.*$)', r'<h1 style="color: #1e40af; margin-top: 35px; margin-bottom: 20px;">\1</h1>', html_report, flags=re.MULTILINE)
        
        # Convert bold text
        html_report = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #374151;">\1</strong>', html_report)
        
        # Convert numbered lists (for sources)
        html_report = re.sub(r'^(\d+\.\s)(.*$)', r'<li style="margin-bottom: 8px; list-style-type: decimal;">\2</li>', html_report, flags=re.MULTILINE)
        
        # Convert bullet points
        html_report = re.sub(r'^- (.*$)', r'<li style="margin-bottom: 8px;">\1</li>', html_report, flags=re.MULTILINE)
        
        # Wrap consecutive list items in ul/ol tags
        html_report = re.sub(r'(<li style="margin-bottom: 8px; list-style-type: decimal;">.*?</li>)', r'<ol style="margin: 15px 0; padding-left: 25px;">\1</ol>', html_report, flags=re.DOTALL)
        html_report = re.sub(r'(<li style="margin-bottom: 8px;">.*?</li>)', r'<ul style="margin: 15px 0; padding-left: 25px;">\1</ul>', html_report, flags=re.DOTALL)
        
        # Convert line breaks
        html_report = html_report.replace('\n\n', '</p><p style="margin-bottom: 15px; line-height: 1.6;">')
        html_report = '<p style="margin-bottom: 15px; line-height: 1.6;">' + html_report + '</p>'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Research Report</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #374151; background-color: #f9fafb; margin: 0; padding: 20px;">
            <div style="max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07); overflow: hidden;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: 600;">
                        🔍 Your Research Report
                    </h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">
                        Comprehensive AI-powered research analysis
                    </p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <div style="background: #f8fafc; padding: 30px; border-radius: 8px; border-left: 4px solid #2563eb; margin-bottom: 30px;">
                        {html_report}
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f8fafc; padding: 25px 30px; border-top: 1px solid #e5e7eb;">
                    <div style="text-align: center; color: #6b7280; font-size: 14px;">
                        <p style="margin: 0 0 10px 0;">
                            <strong>🤖 Generated by Deep Research Assistant</strong>
                        </p>
                        <p style="margin: 0;">
                            This report was created using advanced AI with multi-step quality assurance
                        </p>
                        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #d1d5db;">
                            <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                                Thank you for using our research service • Generated on {__import__('datetime').datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        
        print(f"Email response: {response.status_code}")
        if response.status_code == 202:
            return {"status": f"Email sent successfully to {recipient_email}"}
        else:
            return {"status": f"Email sending failed with status {response.status_code}"}
            
    except Exception as e:
        print(f"Email sending error: {e}")
        return {"status": f"Email sending failed: {str(e)}"}

@function_tool
async def send_report_email_to_address(report: str, recipient_email: str) -> Dict[str, str]:
    """ Send the final research report via email to a specific address """
    return await _send_report_email_to_address(report, recipient_email)

@function_tool
async def send_report_email(report: str) -> Dict[str, str]:
    """ Send the final research report via email (legacy function - uses hardcoded email) """
    print("Sending email to default address...")
    result = await Runner.run(email_agent, report)
    print("Email sent to default address")
    return {"status": "Email sent successfully to default address"}

# Manager Agent Instructions
MANAGER_INSTRUCTIONS = """
You are the Research Manager Agent responsible for orchestrating a comprehensive research process with quality assurance.

Your workflow:

1. **PLAN**: Use plan_research to create a search strategy for the query
2. **SEARCH**: Use perform_search for each planned search item to gather information
3. **INITIAL REPORT**: Use write_initial_report to create a first draft from all search results
4. **EVALUATE**: Use evaluate_report to assess the quality of the initial report
5. **OPTIMIZE** (if needed): If evaluation shows needs_refinement=True, use optimize_report to improve it
6. **FINALIZE**: Use send_report_email_to_address to deliver the final report

Quality Standards:
- Only proceed to email if the report scores 7+ or has been optimized
- If a report needs refinement, always optimize it before sending
- Ensure comprehensive coverage of the original query
- Maintain high standards for accuracy and completeness

Be methodical and ensure each step completes successfully before proceeding to the next.
"""

# Function to create custom research agent with email options
def create_custom_research_agent(email_address: str = None, send_email: bool = False):
    """Create a research manager agent with custom email settings"""
    
    if send_email and email_address:
        # Include email sending in tools
        tools = [
            plan_research,
            perform_search, 
            write_initial_report,
            evaluate_report,
            optimize_report,
            send_report_email_to_address
        ]
        
        instructions = f"""
You are the Research Manager Agent responsible for orchestrating a comprehensive research process with quality assurance.

Your workflow:

1. **PLAN**: Use plan_research to create a search strategy for the query
2. **SEARCH**: Use perform_search for each planned search item to gather information
3. **INITIAL REPORT**: Use write_initial_report to create a first draft from all search results
4. **EVALUATE**: Use evaluate_report to assess the quality of the initial report
5. **OPTIMIZE** (if needed): If evaluation shows needs_refinement=True, use optimize_report to improve it
6. **FINALIZE**: Use send_report_email_to_address with the report and recipient email "{email_address}" to deliver the final report

Quality Standards:
- Only proceed to email if the report scores 7+ or has been optimized
- If a report needs refinement, always optimize it before sending
- Ensure comprehensive coverage of the original query
- Maintain high standards for accuracy and completeness

IMPORTANT: When using send_report_email_to_address, you must provide both:
- The final report text as the first parameter
- The recipient email address "{email_address}" as the second parameter

Be methodical and ensure each step completes successfully before proceeding to the next.
The user has requested the report be emailed to: {email_address}
"""
    else:
        # Exclude email sending from tools
        tools = [
            plan_research,
            perform_search, 
            write_initial_report,
            evaluate_report,
            optimize_report
        ]
        
        instructions = """
You are the Research Manager Agent responsible for orchestrating a comprehensive research process with quality assurance.

Your workflow:

1. **PLAN**: Use plan_research to create a search strategy for the query
2. **SEARCH**: Use perform_search for each planned search item to gather information
3. **INITIAL REPORT**: Use write_initial_report to create a first draft from all search results
4. **EVALUATE**: Use evaluate_report to assess the quality of the initial report
5. **OPTIMIZE** (if needed): If evaluation shows needs_refinement=True, use optimize_report to improve it
6. **COMPLETE**: Return the final optimized report (do NOT send email - user chose not to receive email)

Quality Standards:
- Complete the process when report scores 7+ or has been optimized
- If a report needs refinement, always optimize it before completing
- Ensure comprehensive coverage of the original query
- Maintain high standards for accuracy and completeness

Be methodical and ensure each step completes successfully before proceeding to the next.
The user has chosen NOT to receive the report via email.
"""

    return Agent(
        name=f"Custom Research Manager Agent",
        instructions=instructions,
        tools=tools,
        model="gpt-4o-mini",
        handoff_description="Orchestrate comprehensive research with quality assurance and optional email delivery"
    )

# Create the Research Manager Agent with agents-as-tools
ResearchManagerAgent = Agent(
    name="Research Manager Agent",
    instructions=MANAGER_INSTRUCTIONS,
    tools=[
        plan_research,
        perform_search, 
        write_initial_report,
        evaluate_report,
        optimize_report,
        send_report_email_to_address
    ],
    model="gpt-4o-mini",
    handoff_description="Orchestrate comprehensive research with quality assurance and optimization"
)

async def run_research_with_progress(query: str, email_address: str = None, send_email: bool = False) -> AsyncGenerator[str, None]:
    """Run research with step-by-step progress updates"""
    trace_id = gen_trace_id()
    
    yield f"🚀 **Starting Enhanced Research**\n\n**Query:** {query}\n\n**Trace ID:** {trace_id}\n\n---\n\n"
    
    try:
        with trace("Enhanced Research with Progress", trace_id=trace_id):
            # Step 1: Planning
            yield "📋 **Step 1/6:** Planning research strategy...\n\n*Analyzing your query and determining the best search approach*"
            
            result = await Runner.run(planner_agent, f"Query: {query}")
            search_plan = result.final_output_as(WebSearchPlan)
            
            yield f"✅ **Planning Complete** - Will perform {len(search_plan.searches)} targeted searches\n\n---\n\n"
            
            # Step 2: Searching
            yield "🔍 **Step 2/6:** Conducting web searches...\n\n*Gathering information from multiple sources*"
            
            search_results = []
            for i, search_item in enumerate(search_plan.searches, 1):
                yield f"🔍 **Search {i}/{len(search_plan.searches)}:** {search_item.query}\n\n*{search_item.reason}*"
                
                try:
                    input_text = f"Search term: {search_item.query}\nReason for searching: {search_item.reason}"
                    result = await Runner.run(search_agent, input_text)
                    search_results.append(str(result.final_output))
                    yield f"✅ **Search {i} Complete**\n\n"
                except Exception as e:
                    yield f"⚠️ **Search {i} Failed:** {str(e)}\n\n"
                    search_results.append(f"Search failed: {str(e)}")
            
            yield "✅ **All Searches Complete**\n\n---\n\n"
            
            # Step 3: Writing Initial Report
            yield "✍️ **Step 3/6:** Writing initial research report...\n\n*Analyzing and synthesizing all gathered information*"
            
            combined_results = "\n\n".join(search_results)
            input_text = f"Original query: {query}\nSummarized search results: {combined_results}"
            result = await Runner.run(writer_agent, input_text)
            report_data = result.final_output_as(ReportData)
            
            yield "✅ **Initial Report Complete**\n\n---\n\n"
            
            # Step 4: Evaluating Quality
            yield "🔍 **Step 4/6:** Evaluating report quality...\n\n*AI quality assessment in progress*"
            
            input_text = f"Original Query: {query}\n\nReport to Evaluate:\n{report_data.markdown_report}"
            result = await Runner.run(evaluator_agent, input_text)
            evaluation = result.final_output_as(EvaluationResult)
            
            yield f"✅ **Evaluation Complete** - Score: {evaluation.overall_score}/10\n\n"
            
            final_report = report_data.markdown_report
            
            # Step 5: Optimization (if needed)
            if evaluation.needs_refinement:
                yield "🔧 **Step 5/6:** Optimizing report quality...\n\n*Improving report based on evaluation feedback*"
                
                feedback = f"Score: {evaluation.overall_score}/10\nWeaknesses: {evaluation.weaknesses}\nSuggestions: {evaluation.suggestions}"
                input_text = f"""Original Query: {query}

Original Report:
{report_data.markdown_report}

Evaluation Feedback:
{feedback}

Please improve the report based on this feedback."""
                
                result = await Runner.run(optimizer_agent, input_text)
                optimized = result.final_output_as(OptimizedReport)
                final_report = optimized.improved_markdown_report
                
                yield "✅ **Optimization Complete** - Report quality improved\n\n---\n\n"
            else:
                yield "✅ **No Optimization Needed** - Report quality is excellent\n\n---\n\n"
            
            # Step 6: Email Delivery (if requested)
            if send_email and email_address:
                yield f"📧 **Step 6/6:** Sending report to {email_address}...\n\n*Preparing and delivering your research report*"
                
                try:
                    # Call the regular function directly
                    result = await _send_report_email_to_address(final_report, email_address)
                    yield f"✅ **Email Sent Successfully** to {email_address}\n\n---\n\n"
                except Exception as e:
                    yield f"❌ **Email Failed:** {str(e)}\n\n---\n\n"
            else:
                yield "📄 **Step 6/6:** Finalizing report...\n\n*Email delivery not requested*\n\n---\n\n"
            
            # Final result
            yield f"""🎉 **Research Complete!**

**📊 Final Report:**

{final_report}

**🔗 View Full Trace:** https://platform.openai.com/traces/trace?trace_id={trace_id}

---
*Enhanced research completed with quality assurance*"""
            
    except Exception as e:
        yield f"❌ **Error during research:** {str(e)}"