import asyncio
from agents import Runner, trace, gen_trace_id
from check_planner_agent import check_planner_agent, UrlCheckPlan, UrlCheckItem
from check_agents import check_agent_1, check_agent_2
from check_manager_agent import check_manager_agent
from report_agent import UrlReportData, reporter_agent
from email_agent import email_agent
from typing import Optional, Union
from agents.exceptions import InputGuardrailTripwireTriggered
import gradio as gr

class GeneralManager:
    async def run(self, url: str, email_to: Optional[str] = None):
        trace_id = gen_trace_id()
        with trace("Security url advisor", trace_id=trace_id):
            yield f"Planning checks... View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Planning checks...")
            checks_plan = await self.plan_checks(url, email_to)
            if isinstance(checks_plan, list):
                messages_as_str = [str(msg) for msg in checks_plan]
                combined_msg = "\n".join(f"⚠️ {msg}" for msg in messages_as_str)
                yield combined_msg
                return
            else:
                yield f"Running security checks..."
                checks = await self.run_checks(checks_plan)
                yield f"Generating report..."
                report = await self.report(url, checks)
                if email_to:
                    yield f"Sending email to {email_to}..."
                    try:
                        await self.send_email("wieczoreks@hotmail.com", email_to, report)
                        yield "Email sent successfully ✔️"
                    except Exception as e:
                        print("Email sending failed:", e)
                        yield f"⚠️ Failed to send email to {email_to}. Error: {e}"
                else:
                    yield "No email provided — skipping email delivery."
                yield "Completed report ✅"
                yield report.markdown_report

    async def plan_checks(self, url: str, email_to: Optional[str]) -> Union[UrlCheckPlan, list[str]]:
        """Plan the search to perform the query""" 
        print("Planning the check...")
        try:
            result = await Runner.run(
                check_planner_agent, 
                f"Url: {url}, Email to : {email_to}"
            )
        except InputGuardrailTripwireTriggered as e:
            info = getattr(e, "output_info", {}) or {}
            messages = []

            if info.get("is_url") is False:
                messages.append("URL validation failed.")
            if info.get("is_email") is False:
                messages.append("Email validation failed.")
            if not messages:
                msg_text = str(e)
                if "email" in msg_text.lower():
                    messages.append("Email validation failed.")
                if "url" in msg_text.lower():
                    messages.append("URL validation failed.")
            if not messages:
                messages.append("Guardrail triggered: invalid input detected.")
            print(e, "Guardrail triggered in check planner:", " ".join(messages))
            return messages
        else: 
            print(f"Will perform {len(result.final_output.checks)} searches")
            return result.final_output_as(UrlCheckPlan)
    
    async def run_checks(self, check_plan: UrlCheckPlan) -> list[str]:
        """ Perform all planned checks for the URL """
        print("Performing security checks...")
        num_completed = 0
        tasks = [asyncio.create_task(self.check(item)) for item in check_plan.checks]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed+=1
            print(f"Checking... {num_completed}/{len(tasks)} completed")
        print(f"Finished {num_completed} checks")
        return results

    async def check(self, item: UrlCheckItem) -> str | None:
        """ Perform a check for a single URL aspect using two agents and pick the best result """
        input_text = f"Check: {item.check}\nReason: {item.reason}"
        try:
            # Step 1: Run both security search agents concurrently to get their feedback
            result1, result2 = await asyncio.gather(
            Runner.run(check_agent_1, input_text),
            Runner.run(check_agent_2, input_text)
            )
            # Step 2: Ask the Security Manager agent to pick the best feedback
            search_manager_input = f"""Check: {item.check},
            Reason: {item.reason},
            Feedback from Security Agent 1: {result1.final_output}
            Feedback from Security Agent 2: {result2.final_output}
            Using your judgment, select the single best feedback for this URL check.
            Return only the winning feedback text.
            """
            best_result_response = await Runner.run(check_manager_agent, search_manager_input)
            return best_result_response
        except Exception:
            return None
    async def report(self, url: str, check_results: str) -> UrlReportData:
        """Write report about url"""
        print("Processing report...")
        input = f"Original url: {url}\nSummarized check results: {check_results}"
        result = await Runner.run(reporter_agent,  input)
        print("Completed report")
        return result.final_output_as(UrlReportData)

    async def send_email(self, email_from:str, email_to:str, report: UrlReportData):
        """Send email"""
        print("Sending email...")
        output = f"""
            send email from: {email_from}
            send email to: {email_to}
            report: {report}
        """
        await Runner.run(email_agent, output)
