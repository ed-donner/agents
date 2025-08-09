from agents import Runner, trace, gen_trace_id
from job_search_planner_agent import planner_agent
from job_search_agent import search_agent
from job_matcher_agent import matcher_agent
from job_emailer import email_agent

print("🔧 [MANAGER INIT] JobSearchManager module loaded")

class JobSearchManager:

    async def run(self, resume: str, preferences: str):
        """ Run the job search process """
        print(f"\n🎯 [MANAGER] Starting job search process...")
        print(f"📄 [MANAGER] Resume length: {len(resume)} characters")
        print(f"🎯 [MANAGER] Preferences: {preferences}")
        
        trace_id = gen_trace_id()
        print(f"📊 [MANAGER] Generated trace ID: {trace_id}")
        
        with trace("Job Search trace", trace_id=trace_id):
            yield f"Starting job search..."
            
            # Step 1: Plan searches
            print("🔍 [MANAGER] Step 1: Running planner agent...")
            plan_input = f"Resume: {resume}\nPreferences: {preferences}"
            print(f"📝 [MANAGER] Planner input length: {len(plan_input)} characters")
            
            plan_result = await Runner.run(planner_agent, plan_input)
            print(f"✅ [MANAGER] Planner completed. Found {len(plan_result.final_output.searches)} searches")
            yield "Searching for jobs..."
            
            # Step 2: Search for jobs (simplified - just use first search)
            first_search = plan_result.final_output.searches[0]
            print(f"🔎 [MANAGER] Step 2: Using first search query: '{first_search.query}'")
            print(f"💡 [MANAGER] Search reason: {first_search.reason}")
            
            search_input = f"Search term: {first_search.query}\nReason: {first_search.reason}"
            search_result = await Runner.run(search_agent, search_input)
            print(f"✅ [MANAGER] Search completed. Found {len(search_result.final_output.jobs)} jobs")
            yield "Matching jobs to your profile..."
            
            # Step 3: Match jobs
            print("🎯 [MANAGER] Step 3: Running matcher agent...")
            match_input = f"Resume: {resume}\nJobs: {search_result.final_output.jobs}"
            print(f"📊 [MANAGER] Matcher input: Resume + {len(search_result.final_output.jobs)} jobs")
            
            match_result = await Runner.run(matcher_agent, match_input)
            print(f"✅ [MANAGER] Matching completed. Generated {len(match_result.final_output.matches)} matches")
            yield "Sending email..."
            
            # Step 4: Send email
            print("📧 [MANAGER] Step 4: Formatting and sending email...")
            report = self.format_matches(match_result.final_output)
            print(f"📝 [MANAGER] Report length: {len(report)} characters")
            
            await Runner.run(email_agent, report)
            print("✅ [MANAGER] Email sent successfully")
            yield "Complete!"
            yield report
            
        print("🎉 [MANAGER] Job search process completed successfully")
    
    def format_matches(self, matches):
        """ Format job matches into a readable report """
        print(f"📋 [MANAGER] Formatting {len(matches.matches)} job matches...")
        print(f"📊 [MANAGER] Summary: {matches.summary}")
        
        report = f"# Job Search Results\n\n{matches.summary}\n\n"
        for i, match in enumerate(matches.matches):
            print(f"📝 [MANAGER] Formatting match {i+1}: {match.job_title} at {match.company_name} (Score: {match.match_score})")
            report += f"## {match.job_title} at {match.company_name}\n"
            report += f"**Match Score:** {match.match_score}/100\n\n"
            if match.key_strengths:
                report += "**Key Strengths:**\n"
                for strength in match.key_strengths:
                    report += f"- {strength}\n"
            report += "\n---\n\n"
        
        print(f"✅ [MANAGER] Report formatting completed")
        return report