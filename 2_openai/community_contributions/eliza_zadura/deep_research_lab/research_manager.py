"""
Research Manager - orchestrates the full trust-aware research workflow.

Flow:
1. Intake: Generate questions -> User answers -> Locked brief
2. Planning: Create search strategy with source policy
3. Search: Execute queries, collect raw results
4. Synthesis: Build claim ledger from evidence
5. Writing: Generate report constrained to ledger
6. Email: Send formatted report (optional)
"""

from agents import Runner, trace, gen_trace_id

from models import (
    ResearchBrief,
    FollowUpQuestions,
    SearchPlan,
    ClaimLedger,
    ReportData,
)
from search_executor import SearchResults
from intake_agent import questions_agent, brief_agent
from planner_agent import planner_agent
from search_executor import execute_search_plan
from synthesizer_agent import synthesizer_agent
from writer_agent import writer_agent
from email_agent import email_agent


class ResearchManager:
    """
    Orchestrates the trust-aware research workflow.
    
    Usage:
        manager = ResearchManager()
        
        # Phase 1: Get questions
        questions = await manager.get_intake_questions("AI in healthcare")
        
        # Phase 2: User answers questions, then:
        brief = await manager.create_brief("AI in healthcare", user_answers)
        
        # Phase 3: Run research
        async for status in manager.run_research(brief):
            print(status)
    """
    
    def __init__(self):
        self.trace_id = None
    
    async def get_intake_questions(self, topic: str) -> FollowUpQuestions:
        """
        Phase 1a: Generate follow-up questions for the user.
        
        Args:
            topic: The raw research topic from the user
            
        Returns:
            FollowUpQuestions with 3 clarifying questions
        """
        result = await Runner.run(
            questions_agent,
            f"Research topic: {topic}"
        )
        return result.final_output_as(FollowUpQuestions)
    
    async def create_brief(
        self, 
        topic: str, 
        questions: list[str],
        answers: dict[str, str]
    ) -> ResearchBrief:
        """
        Phase 1b: Create the locked research brief from user answers.
        
        Args:
            topic: The original research topic
            questions: The questions that were asked
            answers: Dict mapping question -> answer
            
        Returns:
            A locked ResearchBrief that guides all downstream work
        """
        # Format the Q&A for the brief agent
        qa_text = "\n".join([
            f"Q: {q}\nA: {answers.get(q, 'Not answered')}"
            for q in questions
        ])
        
        input_text = f"""
Original topic: {topic}

Follow-up questions and answers:
{qa_text}
"""
        result = await Runner.run(brief_agent, input_text)
        return result.final_output_as(ResearchBrief)
    
    async def run_research(self, brief: ResearchBrief, send_email: bool = True):
        """
        Phases 2-6: Execute the full research pipeline.
        
        Args:
            brief: The locked research brief
            send_email: Whether to send the final report via email
            
        Yields:
            Status updates as strings for UI display
        """
        self.trace_id = gen_trace_id()
        
        with trace("Trust-Aware Research", trace_id=self.trace_id):
            trace_url = f"https://platform.openai.com/traces/trace?trace_id={self.trace_id}"
            print(f"View trace: {trace_url}")
            yield f"🔗 [View trace]({trace_url})"
            
            # Phase 2: Plan searches
            yield "📋 Planning search strategy..."
            search_plan = await self._plan_searches(brief)
            yield f"   → {len(search_plan.searches)} queries planned"
            
            # Phase 3: Execute searches
            yield "🔍 Searching..."
            search_results = await self._execute_searches(search_plan)
            yield f"   → {len(search_results.results)} sources collected"
            
            # Phase 4: Synthesize claims
            yield "🧪 Synthesizing claims..."
            claim_ledger = await self._synthesize_claims(brief, search_results)
            yield f"   → {len(claim_ledger.claims)} claims validated"
            if claim_ledger.conflicts:
                yield f"   → {len(claim_ledger.conflicts)} conflicts noted"
            
            # Phase 5: Write report
            yield "✍️ Writing report..."
            report = await self._write_report(brief, claim_ledger)
            yield "   → Report complete"
            
            # Phase 6: Send email (optional)
            if send_email:
                yield "📧 Sending email..."
                await self._send_email(report)
                yield "   → Email sent"
            
            yield "✅ Research complete!"
            yield "---"
            yield report.markdown_report
            yield self._format_claim_ledger(claim_ledger)
    
    async def _plan_searches(self, brief: ResearchBrief) -> SearchPlan:
        """Create the search plan based on the research brief."""
        input_text = f"""
Research Brief:
- Topic: {brief.topic}
- Intended use: {brief.intended_use}
- Scope: {brief.scope_constraints}
- Angle: {brief.desired_angle}
"""
        result = await Runner.run(planner_agent, input_text)
        return result.final_output_as(SearchPlan)
    
    async def _execute_searches(self, plan: SearchPlan) -> SearchResults:
        """Execute all planned searches."""
        return await execute_search_plan(plan)
    
    async def _synthesize_claims(
        self, 
        brief: ResearchBrief, 
        results: SearchResults
    ) -> ClaimLedger:
        """Build the claim ledger from search results."""
        # Format results for the synthesizer with domain and publisher type
        results_text = "\n\n".join([
            f"Source: {r.url}\n"
            f"Domain: {r.domain}\n"
            f"Publisher Type: {r.publisher_type.value}\n"
            f"Tier: {r.inferred_tier.value}\n"
            f"Snippet: {r.snippet}"
            for r in results.results
        ])
        
        input_text = f"""
Research topic: {brief.topic}
Desired angle: {brief.desired_angle}

Search Results:
{results_text}
"""
        result = await Runner.run(synthesizer_agent, input_text)
        return result.final_output_as(ClaimLedger)
    
    async def _write_report(
        self, 
        brief: ResearchBrief, 
        ledger: ClaimLedger
    ) -> ReportData:
        """Generate the final report from the claim ledger."""
        # Format claims for the writer
        claims_text = "\n\n".join([
            f"Claim: {c.claim}\n"
            f"Evidence: {c.evidence}\n"
            f"Source: {c.source_url} ({c.source_tier.value})\n"
            f"Confidence: {c.confidence}\n"
            f"Notes: {c.notes or 'None'}"
            for c in ledger.claims
        ])
        
        conflicts_text = "\n".join(ledger.conflicts) if ledger.conflicts else "None"
        gaps_text = "\n".join(ledger.gaps) if ledger.gaps else "None"
        
        input_text = f"""
Research Brief:
- Topic: {brief.topic}
- Intended use: {brief.intended_use}
- Desired angle: {brief.desired_angle}

Claim Ledger:
{claims_text}

Conflicts to address:
{conflicts_text}

Gaps to acknowledge:
{gaps_text}
"""
        result = await Runner.run(writer_agent, input_text)
        return result.final_output_as(ReportData)
    
    async def _send_email(self, report: ReportData) -> None:
        """Send the report via email."""
        await Runner.run(email_agent, report.markdown_report)
    
    def _format_claim_ledger(self, ledger: ClaimLedger) -> str:
        """Format the claim ledger as markdown for display."""
        lines = ["\n---\n## 📊 Claim Ledger\n"]
        
        for i, c in enumerate(ledger.claims, 1):
            lines.append(f"**{i}. {c.claim}**")
            lines.append(f"- Evidence: {c.evidence}")
            # Format source with domain and publisher type
            domain = c.source_domain or "unknown"
            pub_type = c.source_publisher_type or "unknown"
            lines.append(f"- Source: [{domain}]({c.source_url}) — {pub_type} ({c.source_tier.value})")
            lines.append(f"- Confidence: {c.confidence}")
            if c.notes:
                lines.append(f"- Notes: {c.notes}")
            lines.append("")
        
        if ledger.conflicts:
            lines.append("### ⚠️ Conflicts")
            for conflict in ledger.conflicts:
                lines.append(f"- {conflict}")
            lines.append("")
        
        if ledger.gaps:
            lines.append("### 🔍 Gaps")
            for gap in ledger.gaps:
                lines.append(f"- {gap}")
        
        return "\n".join(lines)
