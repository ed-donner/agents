

from autogen_core import SingleThreadedAgentRuntime
from autogen_core import AgentId
from creator import Creator
from recruiter import DoctorsRecruiter
from evaluator import DoctorsDiagnoseEvaluator
import messages
import asyncio
import json
import os
    
class MedicalPipeline:
    def __init__(self, symptoms: str, host_address="localhost:50051"):
        self.symptoms = symptoms
        self.host_address = host_address
        self.runtime = SingleThreadedAgentRuntime()
        self.is_runtime = False
        self.doctors = []

    def start_runtime(self):
        if not self.is_runtime:
            self.runtime.start()
            return ("🏥 AI Hospital opened... \n")

    async def stop_runtime(self):
        if self.runtime:
            await self.runtime.stop()
            return ("🏥 AI Hospital is closed...\n")

    async def create_and_message(self, creator_id, doctor: dict):
        
        os.makedirs("./output", exist_ok=True)
        doctor_name = doctor["doctor_name"].replace(" ", "")
        speciality = doctor["speciality"].replace(" ", "")
        payload = {
            "filename": f"doctor_{doctor_name}_{speciality}.py",
            "symptoms": self.symptoms,
            "doctors": self.doctors
        }
        result = await self.runtime.send_message( messages.Message(content=json.dumps(payload)), creator_id )
        with open(f"./output/doctor_{doctor_name}_{speciality}.md", "w") as f:
            f.write(result.content)

    async def run(self) -> str:
        status = self.start_runtime()
        yield {
            "content": {"evaluations": [], "chosen": {}}, 
            "status": status
        }
        try:
            await DoctorsRecruiter.register(self.runtime,"DoctorsRecruiter", lambda: DoctorsRecruiter("DoctorsRecruiter"))
            recruiter_id = AgentId("DoctorsRecruiter", "default")
            recruiter_prompt = ( "Get doctors list based on the following patient symptoms: " f"{self.symptoms}")
            response = await self.runtime.send_message(
                messages.Message(content=recruiter_prompt),
                recruiter_id
            )
            self.doctors=json.loads(response.content)["doctors"]
            doctors_names = ''
            for doctor in self.doctors:
                doctors_names+= f"""\nDoctor Name: {doctor["doctor_name"]}, Movie: {doctor["movie"]} \n"""
            yield {
                "content": {"evaluations": [], "chosen": {}}, 
                "status": "🏥 Hired doctors: \n" + doctors_names + "\n"
            }
            await Creator.register(self.runtime,  "Creator", lambda: Creator("Creator"))
            yield {
                "content": {"evaluations": [], "chosen": {}}, 
                "status": "🏥 Doctors focus on diagnosis..."
            }
            creator_id = AgentId("Creator", "default")
            await asyncio.gather(*[
                self.create_and_message(creator_id, doctor)
                for doctor in self.doctors
            ])
            yield {
                "content": {"evaluations": [], "chosen": {}}, 
                "status": "\n🏥 Hospital director is choosing the best diagnosis...\n"
            }
            await DoctorsDiagnoseEvaluator.register(self.runtime, "DoctorsDiagnoseEvaluator", 
                lambda: DoctorsDiagnoseEvaluator("DoctorsDiagnoseEvaluator"))
            evaluator_id = AgentId("DoctorsDiagnoseEvaluator", "default")
            response = await self.runtime.send_message(
                messages.Message( content=f"Assign the best doctor for {self.symptoms} provided"),evaluator_id)
            yield {
                "content": response.content, 
                "status":"\n🏥 Diagnose selection completed \n"
            }
        finally:
            current_status = await self.stop_runtime()
            yield {
                "status": current_status
            }

if __name__ == "__main__":
    async def test():
        pipeline = MedicalPipeline("I have tooth ache")
        last_result = None
        async for result in pipeline.run():
            print(result) 
            last_result = result
        print("Final result:", last_result)

    asyncio.run(test())