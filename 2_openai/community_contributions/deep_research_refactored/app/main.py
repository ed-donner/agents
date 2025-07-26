"""
Simple FastAPI application for the Deep Research Agent System
"""
import logging
import asyncio
import uuid

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

# Import our existing modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents_manager import AgentManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Deep Research Agent System API",
    description="A simple API for automated research using AI agents",
    version="1.0.0"
)

# Global storage for research sessions
research_sessions = {}

# Initialize configuration and agent manager
agent_manager = AgentManager(model_name="gpt-4o-mini")


# Pydantic models for API requests/responses
class ResearchRequest(BaseModel):
    query: str
    model: Optional[str] = "gpt-4o-mini"


class ResearchResponse(BaseModel):
    session_id: str
    status: str
    message: str


class ResearchStatusResponse(BaseModel):
    session_id: str
    status: str
    query: str
    report: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Deep Research Agent System API",
        "version": "1.0.0",
        "endpoints": {
            "POST /research": "Start a new research session",
            "GET /research/{session_id}": "Get research status and results"
        }
    }


@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """Start a new research session"""
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Store session info
        research_sessions[session_id] = {
            "query": request.query,
            "status": "started",
            "created_at": datetime.now(),
            "model": request.model
        }
        
        # Start research in background
        asyncio.create_task(run_research(session_id, request.query, request.model))
        
        logger.info(f"Started research session {session_id} for query: {request.query}")
        
        return ResearchResponse(
            session_id=session_id,
            status="started",
            message="Research session started successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to start research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/{session_id}", response_model=ResearchStatusResponse)
async def get_research_status(session_id: str):
    """Get the status and results of a research session"""
    if session_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Research session not found")
    
    session = research_sessions[session_id]
    
    return ResearchStatusResponse(
        session_id=session_id,
        status=session["status"],
        query=session["query"],
        report=session.get("report"),
        error=session.get("error")
    )


async def run_research(session_id: str, query: str, model: str):
    """Background task to run the research pipeline"""
    try:
        research_sessions[session_id]["status"] = "in_progress"
        
        logger.info(f"Starting research for session {session_id}")
        
        # Update agent manager configuration
        agent_manager.model_name = model
        
        # Run the research pipeline
        report = await agent_manager.run(query)
        
        if report:
            research_sessions[session_id]["status"] = "completed"
            research_sessions[session_id]["report"] = report.markdown_report
            logger.info(f"Research completed for session {session_id}")
        else:
            research_sessions[session_id]["status"] = "failed"
            research_sessions[session_id]["error"] = "Research pipeline failed to produce a report"
            logger.error(f"Research failed for session {session_id}")
            
    except Exception as e:
        research_sessions[session_id]["status"] = "failed"
        research_sessions[session_id]["error"] = str(e)
        logger.error(f"Research pipeline failed for session {session_id}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 