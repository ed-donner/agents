"""Week 3 (CrewAI) deliverable — a minimal two-agent research crew, in one file.

CrewAI is normally config-driven (agents.yaml + tasks.yaml + a @CrewBase class). Here it's the same
primitives inline to stay minimal: two Agents, two Tasks (the second takes the first as `context`),
run in order by a sequential Crew. role/goal/backstory is how you "program" a CrewAI agent.

Run: uv run python research_crew.py "the topic"     (needs OPENAI_API_KEY)
"""
import sys

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

load_dotenv(override=True)
MODEL = "openai/gpt-4o-mini"

researcher = Agent(
    role="Senior Researcher",
    goal="Find the 5 most important, current facts about {topic}",
    backstory="A meticulous analyst who distills a topic down to what actually matters.",
    llm=MODEL,
)
writer = Agent(
    role="Briefing Writer",
    goal="Turn research notes into a crisp one-page briefing on {topic}",
    backstory="An editor who writes tight, skimmable briefings for busy readers.",
    llm=MODEL,
)

research = Task(
    description="Research {topic}. List the 5 key points, each with a one-line why-it-matters.",
    expected_output="5 bullet points, each a fact plus why it matters.",
    agent=researcher,
)
write = Task(
    description="Using the research, write a one-page markdown briefing on {topic}.",
    expected_output="A markdown briefing: title, 2-sentence intro, the 5 points, a closing takeaway.",
    agent=writer,
    context=[research],                 # the writer receives the researcher's output
    output_file="briefing.md",
)

crew = Crew(agents=[researcher, writer], tasks=[research, write], process=Process.sequential)

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or "the current state of agentic AI frameworks"
    print(crew.kickoff(inputs={"topic": topic}))
