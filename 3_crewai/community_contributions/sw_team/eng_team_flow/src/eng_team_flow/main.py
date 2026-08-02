#!/usr/bin/env python
from random import randint

from pydantic import BaseModel
from typing import List
from crewai.flow import Flow, listen, start, router, or_

from eng_team_flow.crews.business.business_crew import BusinessCrew
from eng_team_flow.crews.manager.technical.technical_manager import TechnicalManagerCrew
from eng_team_flow.crews.engineering.software.software_engineer import (
    SoftwareEngineer
)
from eng_team_flow.crews.engineering.tech_lead.tech_lead import (
    TechLead
)


import os


class EngTeamState(BaseModel):
    business_technical_refinement_counter: int = 0
    code_review_counter: int = 0
    business_use_case: str = ""
    provide_more_clarity: bool = False
    clarifications: str = ""
    final_task_details: str = None
    final_code_generated: str = ""
    corrections_needed: str = ""



class EngTeamFlow(Flow[EngTeamState]):
    
    
    @start(
        "provide_more_clarity"
    )
    def generate_business_usecase(self):
        if self.state.business_technical_refinement_counter > 2:
            print("Too many refinements")
            return "refinement_limit_exceeded"
        print("Generating business usecase.")
        result = (
            BusinessCrew()
            .crew()
            .kickoff(
                inputs={
                    "product_name": "Trader's Desk",
                    "competitor_product_name": "Robinhood",
                    "clarifications": self.state.clarifications
                }
            )
        )
        print(f"Business usecase generated: {result}")
        self.state.business_use_case = result["business_use_case"]

    @router(generate_business_usecase)
    def generate_engineering_task_list(self):
        print("Generating engineering task list.")
        result = (
            TechnicalManagerCrew()
            .crew()
            .kickoff(
                inputs={
                    "requirement": self.state.business_use_case
                }
            )
        )
        self.state.clarifications = result["clarification_query"]
        if result["provide_more_clarity"]:
            self.state.business_technical_refinement_counter += 1
            print(
                f"business refinement_counter now is: {self.state.business_technical_refinement_counter}"
            )
            return "provide_more_clarity"
        print(f"type -> result tasks: {type(result['tasks'])}")
        self.state.final_task_details = "\n\n".join(
            [
                f"{task_detail.task_name} \n\n {task_detail.task_description}" for task_detail in result["tasks"]
            ]
        )
        self.state.final_task_details = f"{self.state.business_use_case}\n\n{self.state.final_task_details}"
        return "initiate_code"
    
    @listen(or_("initiate_code", "refactor_changes"))
    def generate_code(self):
        result = (
            SoftwareEngineer(
                output_file_name=f"agent_output/all_code.py"
            )
            .crew()
            .kickoff(
                inputs={
                    "task_details": f"{self.state.final_task_details}\n\n\n{self.state.corrections_needed}"
                }
            )
        )
        self.state.final_code_generated = result.raw
        print("Resetting corrections needed.")
        self.state.corrections_needed = ""
        return "ready_to_review"

    @router(generate_code)
    def review_code(self):
        result = (
            TechLead()
            .crew()
            .kickoff(
                inputs={
                    "code": f"{self.state.final_task_details}\n\n{self.state.final_code_generated}"
                }
            )
        )
        if result["needs_correction"] and self.state.code_review_counter < 2:
            self.state.corrections_needed = result["changes_to_be_made"]
            self.state.code_review_counter += 1
            return "refactor_changes"
        if self.state.code_review_counter >= 3:
            print("Code review limit reached. Hence, exiting.")
        return "all set!"

    

def kickoff():
    os.environ["CREWAI_STORAGE_DIR"] = f"{os.path.abspath(__name__)}/memory"
    print(f"memory storage location: {os.environ["CREWAI_STORAGE_DIR"]}")
    eng_team_flow = EngTeamFlow()
    eng_team_flow.kickoff()


if __name__ == "__main__":
    os.environ["CREWAI_STORAGE_DIR"] = f"{os.path.abspath(__name__)}/memory"
    print(f"memory storage location: {os.environ["CREWAI_STORAGE_DIR"]}")
    kickoff()
