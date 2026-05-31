from agents import Agent

class CoursesOfStudyAgent:
    def __init__(self):
        self.agent = Agent(
            name="Courses of Study Agent",
            model="gpt-4o-mini",
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