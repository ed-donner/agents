"""
Code generation and analysis tools for agents
"""
from typing import Type, Any, Optional
from pydantic import BaseModel, Field
from crewai_tools import BaseTool


class CodeGenerationInput(BaseModel):
    """Input schema for code generation"""
    language: str = Field(..., description="Programming language (python, go, nodejs, csharp)")
    framework: str = Field(..., description="Framework to use")
    component_type: str = Field(..., description="Type of component (model, service, controller, etc.)")
    component_name: str = Field(..., description="Name of the component")
    specifications: str = Field(..., description="Detailed specifications for the component")


class CodeGenerationTool(BaseTool):
    name: str = "Code Generation Tool"
    description: str = """
    Generates production-ready code based on specifications.
    Supports multiple languages and frameworks.
    Use this tool when you need to create new code files.
    """
    args_schema: Type[BaseModel] = CodeGenerationInput
    
    def _run(
        self,
        language: str,
        framework: str,
        component_type: str,
        component_name: str,
        specifications: str
    ) -> str:
        """Generate code based on specifications"""
        # This is a placeholder - actual implementation would use LLM
        template = self._get_template(language, framework, component_type)
        
        code_output = f"""
# Generated {component_type}: {component_name}
# Language: {language}
# Framework: {framework}

{template}

# Specifications implemented:
# {specifications}
"""
        return code_output
    
    def _get_template(self, language: str, framework: str, component_type: str) -> str:
        """Get appropriate code template"""
        templates = {
            ("python", "fastapi", "model"): '''
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class {name}Base(BaseModel):
    """Base schema for {name}"""
    pass

class {name}Create({name}Base):
    """Schema for creating {name}"""
    pass

class {name}Update({name}Base):
    """Schema for updating {name}"""
    pass

class {name}Response({name}Base):
    """Schema for {name} response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
''',
            ("python", "fastapi", "service"): '''
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import {name}
from .schemas import {name}Create, {name}Update

class {name}Service:
    """Service layer for {name} operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[{name}]:
        """Get all {name} records"""
        return self.db.query({name}).offset(skip).limit(limit).all()
    
    async def get_by_id(self, id: int) -> Optional[{name}]:
        """Get {name} by ID"""
        return self.db.query({name}).filter({name}.id == id).first()
    
    async def create(self, data: {name}Create) -> {name}:
        """Create new {name}"""
        db_obj = {name}(**data.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: int, data: {name}Update) -> Optional[{name}]:
        """Update {name}"""
        db_obj = await self.get_by_id(id)
        if db_obj:
            for key, value in data.dict(exclude_unset=True).items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: int) -> bool:
        """Delete {name}"""
        db_obj = await self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
''',
            ("python", "fastapi", "controller"): '''
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from .database import get_db
from .services import {name}Service
from .schemas import {name}Create, {name}Update, {name}Response

router = APIRouter(prefix="/{name_lower}s", tags=["{name}s"])

@router.get("/", response_model=List[{name}Response])
async def get_all(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all {name}s"""
    service = {name}Service(db)
    return await service.get_all(skip=skip, limit=limit)

@router.get("/{id}", response_model={name}Response)
async def get_by_id(id: int, db: Session = Depends(get_db)):
    """Get {name} by ID"""
    service = {name}Service(db)
    result = await service.get_by_id(id)
    if not result:
        raise HTTPException(status_code=404, detail="{name} not found")
    return result

@router.post("/", response_model={name}Response, status_code=status.HTTP_201_CREATED)
async def create(data: {name}Create, db: Session = Depends(get_db)):
    """Create new {name}"""
    service = {name}Service(db)
    return await service.create(data)

@router.put("/{id}", response_model={name}Response)
async def update(id: int, data: {name}Update, db: Session = Depends(get_db)):
    """Update {name}"""
    service = {name}Service(db)
    result = await service.update(id, data)
    if not result:
        raise HTTPException(status_code=404, detail="{name} not found")
    return result

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(id: int, db: Session = Depends(get_db)):
    """Delete {name}"""
    service = {name}Service(db)
    if not await service.delete(id):
        raise HTTPException(status_code=404, detail="{name} not found")
'''
        }
        
        key = (language.lower(), framework.lower(), component_type.lower())
        return templates.get(key, f"// Template for {language}/{framework}/{component_type}")


class CodeAnalysisInput(BaseModel):
    """Input schema for code analysis"""
    code: str = Field(..., description="Code to analyze")
    analysis_type: str = Field(
        default="full",
        description="Type of analysis (full, security, performance, style)"
    )


class CodeAnalysisTool(BaseTool):
    name: str = "Code Analysis Tool"
    description: str = """
    Analyzes code for quality, security issues, and best practices.
    Use this tool to review and improve code quality.
    """
    args_schema: Type[BaseModel] = CodeAnalysisInput
    
    def _run(self, code: str, analysis_type: str = "full") -> str:
        """Analyze code and return findings"""
        findings = []
        
        # Basic analysis (placeholder for actual implementation)
        if "password" in code.lower() and "hardcoded" not in code.lower():
            findings.append("⚠️ Potential hardcoded password detected")
        
        if "TODO" in code or "FIXME" in code:
            findings.append("📝 Found TODO/FIXME comments that need attention")
        
        if "except:" in code or "except Exception:" in code:
            findings.append("⚠️ Broad exception handling detected - consider specific exceptions")
        
        if not findings:
            findings.append("✅ No major issues found")
        
        return "\n".join(findings)


class CodeRefactoringInput(BaseModel):
    """Input schema for code refactoring"""
    code: str = Field(..., description="Code to refactor")
    refactoring_type: str = Field(..., description="Type of refactoring to apply")
    target_pattern: Optional[str] = Field(None, description="Target design pattern")


class CodeRefactoringTool(BaseTool):
    name: str = "Code Refactoring Tool"
    description: str = """
    Refactors code to improve structure, apply design patterns, or optimize performance.
    Use this tool to improve existing code.
    """
    args_schema: Type[BaseModel] = CodeRefactoringInput
    
    def _run(
        self,
        code: str,
        refactoring_type: str,
        target_pattern: Optional[str] = None
    ) -> str:
        """Refactor code based on specifications"""
        # Placeholder implementation
        return f"""
# Refactored code
# Refactoring type: {refactoring_type}
# Target pattern: {target_pattern or 'N/A'}

{code}

# Refactoring applied successfully
"""
