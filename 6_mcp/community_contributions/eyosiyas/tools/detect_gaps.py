from tools.get_standard import get_standards
from models.schema import DetectGapsInput, DetectGapsOutput, StandardStep

def detect_gaps(input: DetectGapsInput) -> DetectGapsOutput:
    standards = get_standards(input.domain, input.process_name)
    user_steps_lower = [s.lower() for s in input.process_steps]
    gaps = [s for s in standards if s.step.lower() not in user_steps_lower]
    return DetectGapsOutput(gaps=gaps)