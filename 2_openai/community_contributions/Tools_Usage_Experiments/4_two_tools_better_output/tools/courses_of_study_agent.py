"""
    The provided prompts and instructions for this system
    should work, and should result in details of courses of 
    study at the university being returned. You could change the 
    main prompt in main.py and have the agent return the university 
    address, phone number or email address when requested
    by the user. If the agent does not return this information,
    perhaps because a weaker model is used by this agent, then you
    might need to tweak the instructions and / or the tool_description
    in order to give the agent more guidance. That is part of the art
    of prompt engineering, this is not programming, it is data science!
"""

from agents import Agent
from pydantic import BaseModel

class CourseOfStudyOutput(BaseModel):
    major: str
    degrees_offered: str
    total_credits: str
    major_credits: str
    thesis_dissertation_requirements: str
    portfolio_requirements: str
    minimum_gpa: str

class CoursesOfStudyAgent:
    def __init__(self):
        self.agent = Agent(
            name="Courses of Study Agent",
            model="gpt-4o-mini",
            output_type=CourseOfStudyOutput,
            instructions=(
                "You are a helpful support agent. You are able to offer "
                "detailed information about courses of study at Gravizot University."

                "Here is the information you are able to provide: "

                "Computer Science"
                "- BS, MS, PhD"
                "- 120 total credits"
                "- 80 major credits"
                "- MS thesis, PhD dissertation"
                "- minimum 3.0 GPA"

                "Graphic Design"
                "- BA, MFA"
                "- 120 total credits"
                "- 70 major credits"
                "- BA portfolio, MFA portfolio"
                "- minimum 2.5 GPA"

                "Electrical Engineering"
                "- BS, MS, PhD"
                "- 120 total credits"
                "- 70 major credits"
                "- MS thesis, PhD dissertation"
                "- minimum 2.5 GPA"

                "Bio-informatics"
                "- BS, MS"
                "- 120 total credits"
                "- 70 major credits"
                "- MS thesis"
                "- minimum 2.5 GPA"

                "Statistics"
                "- BS, MS, PhD"
                "- 120 total credits"
                "- 70 major credits"
                "- MS thesis, PhD dissertation"
                "- minimum 3.0 GPA"

                "Applied Math"
                "- BS, MS, PhD"
                "- 120 total credits"
                "- 80 major credits"
                "- MS thesis, PhD dissertation"
                "- minimum 2.8 GPA"
            )
        )

        self.agent_tool = self.agent.as_tool(
            tool_name="courses_of_study_tool",
            tool_description="Provides detailed information on courses of study (majors) at Gravizot University."
    )