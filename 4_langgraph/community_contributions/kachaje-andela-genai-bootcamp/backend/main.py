import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.models import (
    ChallengeRequest,
    StateResponse,
    BuildResponse,
)
from backend.state_manager import State
from backend.utils.logger import get_logger

logger = get_logger()

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}


@api.post("/api/session", response_model=StateResponse)
async def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "session_id": session_id,
        "state": "challenge",
        "challenge": "",
        "language": "python",
        "plan": "",
        "build_status": "",
    }
    logger.log_session_event("created", session_id)
    logger.log_api_request(
        method="POST",
        path="/api/session",
        session_id=session_id,
        status_code=200,
        response_body=sessions[session_id],
    )
    return sessions[session_id]


@api.post("/api/session/{session_id}/challenge", response_model=StateResponse)
async def submit_challenge(session_id: str, request: ChallengeRequest):
    try:
        if session_id not in sessions:
            logger.log_api_request(
                method="POST",
                path=f"/api/session/{session_id}/challenge",
                session_id=session_id,
                request_body={"challenge": request.challenge},
                status_code=404,
                error="Session not found",
            )
            raise HTTPException(status_code=404, detail="Session not found")

        old_state = sessions[session_id]["state"]
        sessions[session_id]["challenge"] = request.challenge
        sessions[session_id]["language"] = "python"
        sessions[session_id]["state"] = "busy"

        logger.log_state_transition(
            session_id=session_id,
            from_state=old_state,
            to_state="busy",
            context={
                "challenge": (
                    request.challenge[:100] + "..."
                    if len(request.challenge) > 100
                    else request.challenge
                ),
                "language": "python",
            },
        )

        from backend.state_manager import execute_plan_workflow

        state: State = {
            "session_id": session_id,
            "state": "challenge",
            "challenge": request.challenge,
            "language": "python",
            "plan": "",
            "build_status": "",
        }

        logger.logger.info(f"Starting plan workflow for session {session_id}")
        result = execute_plan_workflow(state)
        sessions[session_id].update(result)
        sessions[session_id]["state"] = "plan"

        logger.log_state_transition(
            session_id=session_id,
            from_state="busy",
            to_state="plan",
            context={"plan_length": len(result.get("plan", ""))},
        )

        logger.log_api_request(
            method="POST",
            path=f"/api/session/{session_id}/challenge",
            session_id=session_id,
            request_body={"challenge": request.challenge},
            status_code=200,
            response_body=sessions[session_id],
        )

        return sessions[session_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.log_api_request(
            method="POST",
            path=f"/api/session/{session_id}/challenge",
            session_id=session_id,
            request_body={"challenge": request.challenge},
            error=str(e),
        )
        raise


@api.get("/api/session/{session_id}/state", response_model=StateResponse)
async def get_state(session_id: str):
    try:
        if session_id not in sessions:
            logger.log_api_request(
                method="GET",
                path=f"/api/session/{session_id}/state",
                session_id=session_id,
                status_code=404,
                error="Session not found",
            )
            raise HTTPException(status_code=404, detail="Session not found")

        logger.log_api_request(
            method="GET",
            path=f"/api/session/{session_id}/state",
            session_id=session_id,
            status_code=200,
            response_body=sessions[session_id],
        )
        return sessions[session_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.log_api_request(
            method="GET",
            path=f"/api/session/{session_id}/state",
            session_id=session_id,
            error=str(e),
        )
        raise


@api.post("/api/session/{session_id}/build", response_model=BuildResponse)
async def build_project(session_id: str):
    try:
        if session_id not in sessions:
            logger.log_api_request(
                method="POST",
                path=f"/api/session/{session_id}/build",
                session_id=session_id,
                status_code=404,
                error="Session not found",
            )
            raise HTTPException(status_code=404, detail="Session not found")

        old_state = sessions[session_id]["state"]
        sessions[session_id]["state"] = "busy"

        logger.log_state_transition(
            session_id=session_id,
            from_state=old_state,
            to_state="busy",
            context={"action": "build"},
        )

        from backend.file_creator import create_project

        logger.logger.info(f"Starting project build for session {session_id}")
        build_result = create_project(
            sessions[session_id]["plan"], sessions[session_id]["language"], session_id
        )

        sessions[session_id]["build_status"] = build_result["status"]
        sessions[session_id]["state"] = "build"

        logger.log_state_transition(
            session_id=session_id,
            from_state="busy",
            to_state="build",
            context={
                "status": build_result["status"],
                "files_count": len(build_result.get("files_created", [])),
            },
        )

        response = BuildResponse(
            session_id=session_id,
            files_created=build_result["files_created"],
            files_skipped=build_result.get("files_skipped", []),
            project_path=build_result["project_path"],
            status=build_result["status"],
        )

        logger.log_api_request(
            method="POST",
            path=f"/api/session/{session_id}/build",
            session_id=session_id,
            status_code=200,
            response_body={
                "session_id": response.session_id,
                "files_created": response.files_created,
                "project_path": response.project_path,
                "status": response.status,
            },
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.log_api_request(
            method="POST",
            path=f"/api/session/{session_id}/build",
            session_id=session_id,
            error=str(e),
        )
        logger.logger.error(f"Error in build_project: {str(e)}", exc_info=True)
        raise


@api.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        logger.log_session_event("deleted", session_id)
        del sessions[session_id]
        logger.log_api_request(
            method="DELETE",
            path=f"/api/session/{session_id}",
            session_id=session_id,
            status_code=200,
            response_body={"status": "cleared"},
        )
    else:
        logger.log_api_request(
            method="DELETE",
            path=f"/api/session/{session_id}",
            session_id=session_id,
            status_code=200,
            response_body={"status": "cleared"},
            error="Session not found (already cleared)",
        )
    return {"status": "cleared"}
