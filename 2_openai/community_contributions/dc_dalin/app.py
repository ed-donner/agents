import gradio as gr
from dotenv import load_dotenv
from agents import Runner
from analyzer_agent import analyzer_agent, SkillBreakdown
from search_agent import search_agent
from project_agent import project_agent, Projects
from writer_agent import writer_agent
import asyncio

load_dotenv(override=True)

async def generate(skill: str, hours: int):
    if not skill or len(skill.strip()) < 3:
        yield "Enter a valid skill"
        return

    try:
        yield "Analyzing skill..."

        breakdown_result = await Runner.run(analyzer_agent, f"Skill: {skill}")
        breakdown = breakdown_result.final_output_as(SkillBreakdown)

        yield "Searching for resources..."

        searches = [f"best {area} resources" for area in breakdown.core_areas[:3]]
        tasks = [search(q) for q in searches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        resources = [r for r in results if isinstance(r, str) and r]

        yield "Designing projects..."

        project_result = await Runner.run(project_agent, f"Skill: {skill}\nAreas: {', '.join(breakdown.core_areas)}")
        projects = project_result.final_output_as(Projects)

        yield "Writing learning path..."

        context = f"""Skill: {skill}
Prerequisites: {breakdown.prerequisites}
Core Areas: {breakdown.core_areas}
Resources: {resources}
Projects: {[p.model_dump() for p in projects.projects]}
Hours/week: {hours}"""

        result = await Runner.run(writer_agent, context)

        yield result.final_output.content
    except Exception as e:
        yield f"Error: {str(e)}"

async def search(query: str):
    try:
        result = await Runner.run(search_agent, query)
        return str(result.final_output)
    except:
        return ""

with gr.Blocks() as app:
    gr.Markdown("# Learning Path Generator")

    skill = gr.Textbox(label="Skill", placeholder="Python, React, Spanish...")
    hours = gr.Slider(1, 20, value=5, label="Hours/week")
    btn = gr.Button("Generate", variant="primary")
    output = gr.Markdown()

    btn.click(generate, [skill, hours], output)
    skill.submit(generate, [skill, hours], output)

app.launch(inbrowser=True)
