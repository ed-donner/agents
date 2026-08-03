from langchain_openai import ChatOpenAI
from state import ResearchState
from pydantic import BaseModel, Field

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class HtmlReport(BaseModel):
    html_content: str = Field(description="The full report, converted to a single HTML string.")

def html_converter_node(state: ResearchState) -> ResearchState:
    print("EXECUTING: HTML CONVERTER NODE")
    
    final_report = state.best_report or state.report
    if not final_report:
        state.final_status += "\nSkipping HTML conversion: No report."
        return state

    prompt = f"""
    You are an expert Markdown-to-HTML converter.
    Convert the following Markdown report into a single, clean, well-structured HTML string.
    Do not add any commentary. Only output the HTML.
    
    Markdown Report: {final_report}
    """
    
    try:
        structured_llm = llm.with_structured_output(HtmlReport)
        result = structured_llm.invoke(prompt)
        state.report_html = result.html_content
        print("  Successfully converted report to HTML.")
    except Exception as e:
        print(f"  Error converting to HTML: {e}")
        state.final_status += f"\nError converting to HTML: {e}"
    
    return state