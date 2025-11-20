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
    code_summary: str = ""



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
        self.state.final_task_details = result["tasks"]
        return "initiate_code"
    
    @listen("initiate_code")
    def generate_code(self):
        for task_detail in self.state.final_task_details:
            print(f"Working on {task_detail.task_name} having {task_detail.task_description}")
            task_description = task_detail.task_description
            is_final = False
            corrections_needed = ""
            code_review_counter = 0
            prev_task_code_summary = ""
            while not is_final:
                result = (
                    SoftwareEngineer(
                        output_file_name=f"agent_output/{task_detail.task_name}.py"
                    )
                    .crew()
                    .kickoff(
                        inputs={
                            "task_details": f"{task_description}\n\n\n{corrections_needed}\n\n\n prev task code summ: {prev_task_code_summary}"
                        }
                    )
                )
                corrections_needed = ""
                prev_task_code_summary = result["code_summary"]
                if not result["needs_correction"]:
                    print("Result generated is correct. Hence, exiting the loop.")
                    is_final = True
                if result["needs_correction"] and code_review_counter < 2:
                    corrections_needed = result["changes_to_be_made"]
                    code_review_counter += 1
                if code_review_counter >= 2:
                    print("Code review limit reached. Hence, exiting.")
                    is_final = True
                
        return
    

def kickoff():
    os.environ["CREWAI_STORAGE_DIR"] = f"{os.path.abspath(__name__)}/memory"
    print(f"memory storage location: {os.environ["CREWAI_STORAGE_DIR"]}")
    eng_team_flow = EngTeamFlow()
    eng_team_flow.kickoff()


if __name__ == "__main__":
    os.environ["CREWAI_STORAGE_DIR"] = f"{os.path.abspath(__name__)}/memory"
    print(f"memory storage location: {os.environ["CREWAI_STORAGE_DIR"]}")
    kickoff()
