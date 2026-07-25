from pydantic import BaseModel, Field

class BugFinding(BaseModel):
    """A bug finding in the codebase"""
    file_path: str = Field(..., description="The file where the bug was found")
    line_number: str = Field(..., description="The specific line or range of lines")
    severity: str = Field(..., description="One of CRITICAL, HIGH, MEDIUM, or LOW")
    category: str = Field(..., description="The bug category from the list above")
    description: str = Field(..., description="A clear explanation of what the bug is")
    suggestion: str = Field(..., description="A brief recommendation on how to fix it")

class BugDetectionOutput(BaseModel):
    """A list of bug findings in the codebase"""
    bugs: list[BugFinding] = Field(..., description="A list of bug findings in the codebase")

class BugGuardrailResult(BaseModel):
    """The result of the bug detection guardrail"""
    passed: bool = Field(..., description="Whether the bug detection guardrail passed")
    reason: str = Field(..., description="The reason for the pass or failure")

class CodeMap(BaseModel):
    """A structured code map"""
    file_path: str = Field(..., description="The file path")
    classes: list[str] = Field(..., description="A list of classes")
    functions: list[str] = Field(..., description="A list of functions")
    imports: list[str] = Field(..., description="A list of imports")
    line_count: int = Field(..., description="The number of lines of code")

class CodeChunk(BaseModel):
    """A code chunk"""
    file_path: str = Field(..., description="The file path")
    start_line: int = Field(..., description="The start line")
    end_line: int = Field(..., description="The end line")
    content: str = Field(..., description="The content of the code chunk")

class CodeAnalysisOutput(BaseModel):
    """A structured code analysis output"""
    code_map: list[CodeMap] = Field(..., description="A list of code maps")

class RefactorSuggestion(BaseModel):
    """A refactor suggestion for the codebase"""
    file_path: str = Field(..., description="The file where the issue was found")
    line_number: str = Field(..., description="The specific line or range of lines")
    priority: str = Field(..., description="One of HIGH, MEDIUM, or LOW")
    category: str = Field(..., description="The quality issue category from the list above")
    description: str = Field(..., description="A clear explanation of why this is a quality concern")
    suggestion: str = Field(..., description="A specific, actionable recommendation with a brief code example where helpful")

class RefactorSuggestionOutput(BaseModel):
    """A list of refactor suggestions for the codebase"""
    refactor_suggestions: list[RefactorSuggestion] = Field(..., description="A list of refactor suggestions for the codebase")

class ReportCompilerOutput(BaseModel):
    """A report compiler output"""
    report_path: str = Field(..., description="The path to the generated report")
    executive_summary: str = Field(..., description="The executive summary of the report")

class SecurityFinding(BaseModel):
    """A security finding in the codebase"""
    file_path: str = Field(..., description="The file where the vulnerability was found")
    line_number: str = Field(..., description="The specific line or range of lines")
    severity: str = Field(..., description="One of CRITICAL, HIGH, MEDIUM, or LOW")
    category: str = Field(..., description="The vulnerability category from the list above")
    description: str = Field(..., description="A clear explanation of what the vulnerability is and how it could be exploited")
    recommendation: str = Field(..., description="A specific, actionable fix or mitigation")

class SecurityAuditOutput(BaseModel):
    """A list of security findings in the codebase"""
    security_findings: list[SecurityFinding] = Field(..., description="A list of security findings in the codebase")

class SecurityGuardrailResult(BaseModel):
    """The result of the security audit guardrail"""
    passed: bool = Field(..., description="Whether the security audit guardrail passed")
    reason: str = Field(..., description="The reason for the pass or failure")

class UserInputAnalysis(BaseModel):
    """The result of the user input analysis"""
    has_repo_reference: bool        
    extracted_value: str            
    input_type: str                 
    reason: str                     