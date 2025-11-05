from agents import Runner, trace, gen_trace_id
from research_agents.clarification_agent import clarification_agent, ClarifyingQuestions
from research_agents.planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from research_agents.search_agent import search_agent
from research_agents.evaluator_agent import evaluator_agent, SearchEvaluation
from research_agents.writer_agent import writer_agent, ReportData
from research_agents.email_agent import email_agent
import asyncio


class ResearchManager:
    """
    Orchestrates the deep research process with clarification and email integration
    This is the manager agent that coordinates all other agents
    """
    
    def __init__(self, user_email: str):
        """
        Initialize the research manager with user's email
        
        Args:
            user_email: Email address where the report will be sent
        """
        self.user_email = user_email
    
    async def get_clarifications(self, query: str):
        """
        Step 1: Ask clarifying questions to better understand user's needs
        
        Args:
            query: The research query from the user
            
        Yields:
            dict: Clarifying questions for the user to answer
        """
        print("Generating clarifying questions...")
        yield {
            "type": "status",
            "message": "Analyzing your query and generating clarifying questions..."
        }
        
        result = await Runner.run(
            clarification_agent,
            f"Research query: {query}",
        )
        
        questions = result.final_output_as(ClarifyingQuestions)
        print(f"Generated clarifying questions")
        
        yield {
            "type": "questions",
            "questions": questions,
            "message": "Questions ready"
        }
    
    async def run(self, query: str, answers: dict):
        """
        Run the deep research process with clarifications, yielding status updates
        
        Args:
            query: The research query from the user
            answers: Dictionary with email and answers to the 3 clarifying questions
            
        Yields:
            dict: Status updates with 'type' and 'message' keys
        """
        # Update email from answers
        self.user_email = answers.get('email', self.user_email)
        
        trace_id = gen_trace_id()
        
        try:
            with trace("Research trace", trace_id=trace_id):
                # Trace information
                trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
                print(f"View trace: {trace_url}")
                yield {
                    "type": "status",
                    "message": f"Trace ID: {trace_id}\nView at: {trace_url}\n\nStarting research with your clarifications..."
                }
                
                # Step 2: Plan searches (using clarifications)
                yield {"type": "status", "message": "Planning search strategy based on your answers..."}
                search_plan = await self.plan_searches(query, answers)
                
                yield {
                    "type": "status",
                    "message": f"Search plan ready.\n\nStrategy: {search_plan.strategy_summary}\n\nWill perform {len(search_plan.searches)} targeted searches"
                }
                
                # Step 3: Perform searches with evaluation
                yield {"type": "status", "message": "Searching the web...\n\nGathering information from multiple sources..."}
                search_results = await self.perform_searches(search_plan)
                
                yield {
                    "type": "status",
                    "message": f"Initial search complete.\n\nCollected {len(search_results)} results. Evaluating quality..."
                }
                
                # Step 3.5: Evaluate search quality
                evaluation = await self.evaluate_searches(query, answers, search_results)
                
                if not evaluation.is_satisfactory and evaluation.suggestions:
                    yield {
                        "type": "status",
                        "message": f"Quality check: Some gaps found (score: {evaluation.quality_score}/10).\n\nPerforming additional searches to fill gaps..."
                    }
                    
                    # Perform additional searches
                    additional_results = await self.perform_additional_searches(evaluation.suggestions)
                    search_results.extend(additional_results)
                    
                    yield {
                        "type": "status",
                        "message": f"Additional searches complete.\n\nTotal results: {len(search_results)} summaries"
                    }
                else:
                    yield {
                        "type": "status",
                        "message": f"Quality check passed (score: {evaluation.quality_score}/10).\n\nReady to write report."
                    }
                
                # Step 4: Write report (incorporating clarifications)
                yield {"type": "status", "message": "Writing comprehensive report...\n\nAnalyzing and synthesizing information based on your specific interests..."}
                report = await self.write_report(query, answers, search_results)
                
                yield {
                    "type": "status",
                    "message": "Report complete.\n\nCustomized to your specific needs"
                }
                
                # Display the report
                yield {"type": "report", "message": report.markdown_report}
                
                # Step 5: Send email
                yield {
                    "type": "status",
                    "message": "Sending email..."
                }
                
                email_result = await self.send_email(report)
                
                if email_result:
                    yield {
                        "type": "email",
                        "message": f"Email sent successfully.\n\nCheck your inbox at {self.user_email}"
                    }
                    yield {
                        "type": "status",
                        "message": "Research complete.\n\nCheck your email for the full report."
                    }
                else:
                    yield {
                        "type": "email",
                        "message": "Email sending failed.\n\nPlease check the report above."
                    }
                    
        except Exception as e:
            print(f"Error in research process: {str(e)}")
            yield {"type": "error", "message": f"An error occurred: {str(e)}"}
    
    async def plan_searches(self, query: str, answers: dict) -> WebSearchPlan:
        """
        Plan the searches using the query and user's clarifications
        
        Args:
            query: The research query
            answers: User's answers to clarifying questions
            
        Returns:
            WebSearchPlan: Planned web searches tuned to user's needs
        """
        print("Planning searches with clarifications...")
        
        # Format the clarifications for the planner
        clarifications_text = f"""
Original Query: {query}

Clarifying Questions and Answers:
1. Q: {answers.get('question_1', 'N/A')}
   A: {answers.get('answer_1', 'Not answered')}

2. Q: {answers.get('question_2', 'N/A')}
   A: {answers.get('answer_2', 'Not answered')}

3. Q: {answers.get('question_3', 'N/A')}
   A: {answers.get('answer_3', 'Not answered')}

Based on these clarifications, create a search strategy that addresses what the user actually wants to know.
"""
        
        result = await Runner.run(
            planner_agent,
            clarifications_text,
        )
        
        plan = result.final_output_as(WebSearchPlan)
        print(f"Planned {len(plan.searches)} searches tuned to user's needs")
        return plan
    
    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """
        Perform the searches concurrently
        
        Args:
            search_plan: The planned web searches
            
        Returns:
            list[str]: Search result summaries
        """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        
        print("Finished searching")
        return results
    
    async def search(self, item: WebSearchItem) -> str | None:
        """
        Perform a single search
        
        Args:
            item: Search item with query and reason
            
        Returns:
            str | None: Search result summary or None if failed
        """
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input_text,
            )
            return str(result.final_output)
        except Exception as e:
            print(f"Search failed for '{item.query}': {str(e)}")
            return None
    
    async def write_report(self, query: str, answers: dict, search_results: list[str]) -> ReportData:
        """
        Write a comprehensive report from the search results and clarifications
        
        Args:
            query: Original research query
            answers: User's answers to clarifying questions
            search_results: List of search result summaries
            
        Returns:
            ReportData: Generated report with summary and follow-up questions
        """
        print("Writing report...")
        
        # Format clarifications for the writer
        clarifications_text = f"""
Clarifications:
1. Q: {answers.get('question_1', 'N/A')}
   A: {answers.get('answer_1', 'Not answered')}

2. Q: {answers.get('question_2', 'N/A')}
   A: {answers.get('answer_2', 'Not answered')}

3. Q: {answers.get('question_3', 'N/A')}
   A: {answers.get('answer_3', 'Not answered')}
"""
        
        input_text = f"""Original query: {query}

{clarifications_text}

Summarized search results: {search_results}

Write a report that directly addresses what the user wants to know based on their clarifications.
"""
        
        result = await Runner.run(
            writer_agent,
            input_text,
        )
        
        print("Finished writing report")
        return result.final_output_as(ReportData)
    
    async def evaluate_searches(self, query: str, answers: dict, search_results: list[str]) -> SearchEvaluation:
        """
        Evaluate if search results are sufficient
        
        Args:
            query: Original research query
            answers: User's clarifications
            search_results: Search result summaries
            
        Returns:
            SearchEvaluation: Evaluation of search quality
        """
        print("Evaluating search quality...")
        
        clarifications_text = f"""
Clarifications:
1. Q: {answers.get('question_1', 'N/A')}
   A: {answers.get('answer_1', 'Not answered')}

2. Q: {answers.get('question_2', 'N/A')}
   A: {answers.get('answer_2', 'Not answered')}

3. Q: {answers.get('question_3', 'N/A')}
   A: {answers.get('answer_3', 'Not answered')}
"""
        
        input_text = f"""Original query: {query}

{clarifications_text}

Search results obtained:
{search_results}

Evaluate if these results are sufficient to write a comprehensive report addressing the user's needs.
"""
        
        result = await Runner.run(
            evaluator_agent,
            input_text,
        )
        
        evaluation = result.final_output_as(SearchEvaluation)
        print(f"Evaluation: {'Satisfactory' if evaluation.is_satisfactory else 'Needs improvement'} (score: {evaluation.quality_score}/10)")
        return evaluation
    
    async def perform_additional_searches(self, search_queries: list[str]) -> list[str]:
        """
        Perform additional searches to fill gaps
        
        Args:
            search_queries: List of search queries to perform
            
        Returns:
            list[str]: Additional search result summaries
        """
        print(f"Performing {len(search_queries)} additional searches...")
        
        from research_agents.planner_agent import WebSearchItem
        
        # Convert string queries to WebSearchItem format
        items = [WebSearchItem(query=q, reason="Filling information gap") for q in search_queries[:3]]  # Limit to 3 additional
        
        tasks = [asyncio.create_task(self.search(item)) for item in items]
        results = []
        
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
        
        print(f"Additional searches complete: {len(results)} results")
        return results
    
    async def send_email(self, report: ReportData) -> bool:
        """
        Send the report via email to the user
        
        Args:
            report: The research report to send
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        print(f"Sending email to {self.user_email}...")
        try:
            result = await Runner.run(
                email_agent,
                f"User email: {self.user_email}\n\nReport:\n{report.markdown_report}",
            )
            print("Email sent successfully")
            return True
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False
