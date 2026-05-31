from models.schema import AnalyzeProcessInput, AnalyzeProcessOutput

def analyze_process(input: AnalyzeProcessInput) -> AnalyzeProcessOutput:
    steps = [step.strip() for step in input.process_steps if step.strip()]
    summary = f"Process contains {len(steps)} steps."
    return AnalyzeProcessOutput(structured_steps=steps, summary=summary)