from mcp.server import FastMCP
from tools.analayze import analyze_process
from tools.detect_gaps import detect_gaps
from tools.generate_recommendations import generate_recommendations
from tools.redesign_process import redesign_process
from models.schema import (
    AnalyzeProcessInput, AnalyzeProcessOutput,
    DetectGapsInput, DetectGapsOutput,
    GenerateRecommendationsInput, GenerateRecommendationsOutput,
    RedesignProcessInput, RedesignProcessOutput
)

mcp = FastMCP(name="consultant_ai_mcp")

@mcp.tool()
def tool_analyze_process(input: AnalyzeProcessInput) -> AnalyzeProcessOutput:
    return analyze_process(input)

@mcp.tool()
def tool_detect_gaps(input: DetectGapsInput) -> DetectGapsOutput:
    return detect_gaps(input)

@mcp.tool()
def tool_generate_recommendations(input: GenerateRecommendationsInput) -> GenerateRecommendationsOutput:
    return generate_recommendations(input)

@mcp.tool()
def tool_redesign_process(input: RedesignProcessInput) -> RedesignProcessOutput:
    return redesign_process(input)

if __name__ == "__main__":
    mcp.run(transport="stdio")  # Use stdio transport for LLM agents