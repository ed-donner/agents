from typing import List, Any, Optional
from typing_extensions import TypedDict
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    code_diff: Optional[str]
    language: Optional[str]
    bug_findings: list[str]
    style_findings: list[str]
    final_review: str

class CodeDiff(BaseModel):
    code_diff: Optional[str] = Field(default=None, description="The code diff to be reviewed, if present in the conversation")
    language: Optional[str] = Field(default=None, description="The programming language of the code diff, if present in the conversation")
    reply_content: str = Field(description="The content of your message in response to the user")
    @property
    def has_diff(self) -> bool:
        return self.code_diff is not None

class BugFinding(BaseModel):
    description: str = Field(description="Description of the bug")
    line_number: int = Field(description="Line number where the bug is found")
    severity: str = Field(description="Severity of the bug (e.g., low, medium, high)")

    def __str__(self):
        return f"description: {self.description}, line_number: {self.line_number}, severity: {self.severity}"

class BugFindings(BaseModel):
    bug_findings: list[BugFinding] = Field(description="List of bug findings")

    def __str__(self):
        return "\n".join(str(finding) for finding in self.bug_findings)

class StyleFinding(BaseModel):
    description: str = Field(description="Description of the style issue")
    line_number: int = Field(description="Line number where the style issue is found")
    severity: str = Field(description="Severity of the style issue (e.g., low, medium, high)")

    def __str__(self):
        return f"description: {self.description}, line_number: {self.line_number}, severity: {self.severity}"

class StyleFindings(BaseModel):
    style_findings: list[StyleFinding] = Field(description="List of style findings")

    def __str__(self):
        return "\n".join(str(finding) for finding in self.style_findings)
    
class FinalReview(BaseModel):
    final_review: str = Field(description="Final review of the code changes")