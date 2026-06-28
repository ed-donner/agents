import logging
import json
from pathlib import Path
from typing import Any, Dict, Optional
import colorlog


class CodeBuilderLogger:
    def __init__(
        self,
        log_dir: str = "logs",
        log_file: Optional[str] = None,
        console: bool = True,
        log_level: str = "INFO",
    ):
        base_dir = Path(__file__).parent.parent.parent
        self.log_dir = base_dir / log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = Path(log_file) if log_file else self.log_dir / "codebuilder.log"
        self.console = console
        self.log_level = getattr(logging, log_level.upper())

        self.logger = logging.getLogger("codebuilder")
        self.logger.setLevel(self.log_level)
        self.logger.handlers.clear()

        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(self.log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        if self.console:
            console_handler = colorlog.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message)s",
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bold",
                },
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        self.logger.propagate = False

    def log_api_request(
        self,
        method: str,
        path: str,
        session_id: Optional[str] = None,
        request_body: Optional[Any] = None,
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
        error: Optional[str] = None,
    ):
        log_parts = [f"API Request: {method} {path}"]

        if session_id:
            log_parts.append(f"Session: {session_id}")

        if request_body is not None:
            if isinstance(request_body, (dict, list)):
                request_body_str = json.dumps(request_body, indent=2)
            else:
                request_body_str = str(request_body)
            log_parts.append(f"Request Body:\n{request_body_str}")

        if status_code is not None:
            log_parts.append(f"Status: {status_code}")

        if response_body is not None:
            if isinstance(response_body, (dict, list)):
                response_body_str = json.dumps(response_body, indent=2)
            else:
                response_body_str = str(response_body)
            log_parts.append(f"Response Body:\n{response_body_str}")

        if error:
            log_parts.append(f"Error: {error}")

        log_message = " | ".join(log_parts)

        if error:
            self.logger.error(
                log_message,
                extra={
                    "method": method,
                    "path": path,
                    "session_id": session_id,
                    "request_body": request_body,
                    "error": error,
                },
            )
        else:
            self.logger.info(
                log_message,
                extra={
                    "method": method,
                    "path": path,
                    "session_id": session_id,
                    "request_body": request_body,
                    "status_code": status_code,
                    "response_body": response_body,
                },
            )

    def log_llm_call(
        self,
        model: str,
        prompt_preview: str,
        response: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ):
        log_parts = [f"LLM Call: model={model}"]

        if prompt_preview:
            preview = (
                prompt_preview[:200] + "..."
                if len(prompt_preview) > 200
                else prompt_preview
            )
            log_parts.append(f"Prompt preview: {preview}")

        if duration_ms is not None:
            log_parts.append(f"Duration: {duration_ms:.2f}ms")

        if error:
            log_parts.append(f"Error: {error}")
            self.logger.error(
                " | ".join(log_parts),
                extra={
                    "model": model,
                    "prompt_preview": prompt_preview,
                    "error": error,
                    "duration_ms": duration_ms,
                },
            )
        else:
            if response:
                response_preview = (
                    response[:200] + "..." if len(response) > 200 else response
                )
                log_parts.append(f"Response preview: {response_preview}")
            self.logger.info(
                " | ".join(log_parts),
                extra={
                    "model": model,
                    "prompt_preview": prompt_preview,
                    "response": response,
                    "duration_ms": duration_ms,
                },
            )

    def log_file_operation(
        self,
        operation: str,
        file_path: str,
        success: bool = True,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        log_parts = [f"File Operation: {operation}", f"Path: {file_path}"]

        if details:
            for key, value in details.items():
                log_parts.append(f"{key}: {value}")

        if error:
            log_parts.append(f"Error: {error}")
            self.logger.error(
                " | ".join(log_parts),
                extra={
                    "operation": operation,
                    "file_path": file_path,
                    "success": False,
                    "error": error,
                    "details": details,
                },
            )
        elif success:
            self.logger.info(
                " | ".join(log_parts),
                extra={
                    "operation": operation,
                    "file_path": file_path,
                    "success": True,
                    "details": details,
                },
            )

    def log_state_transition(
        self,
        session_id: str,
        from_state: str,
        to_state: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        log_parts = [
            f"State Transition: {from_state} -> {to_state}",
            f"Session: {session_id}",
        ]

        if context:
            for key, value in context.items():
                log_parts.append(f"{key}: {value}")

        self.logger.info(
            " | ".join(log_parts),
            extra={
                "session_id": session_id,
                "from_state": from_state,
                "to_state": to_state,
                "context": context,
            },
        )

    def log_web_search(
        self,
        query: str,
        language: Optional[str] = None,
        results_count: Optional[int] = None,
        error: Optional[str] = None,
    ):
        log_parts = [f"Web Search: query='{query}'"]

        if language:
            log_parts.append(f"Language: {language}")

        if results_count is not None:
            log_parts.append(f"Results: {results_count}")

        if error:
            log_parts.append(f"Error: {error}")
            self.logger.error(
                " | ".join(log_parts),
                extra={
                    "query": query,
                    "language": language,
                    "results_count": results_count,
                    "error": error,
                },
            )
        else:
            self.logger.info(
                " | ".join(log_parts),
                extra={
                    "query": query,
                    "language": language,
                    "results_count": results_count,
                },
            )

    def log_session_event(
        self,
        event: str,
        session_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        log_parts = [f"Session Event: {event}", f"Session ID: {session_id}"]

        if details:
            for key, value in details.items():
                log_parts.append(f"{key}: {value}")

        self.logger.info(
            " | ".join(log_parts),
            extra={
                "event": event,
                "session_id": session_id,
                "details": details,
            },
        )

    def log_workflow_node(
        self,
        node_name: str,
        session_id: str,
        state: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        log_parts = [f"Workflow Node: {node_name}", f"Session: {session_id}"]

        if state:
            state_str = json.dumps(state, indent=2)
            log_parts.append(f"State:\n{state_str}")

        if error:
            log_parts.append(f"Error: {error}")
            self.logger.error(
                " | ".join(log_parts),
                extra={
                    "node_name": node_name,
                    "session_id": session_id,
                    "state": state,
                    "error": error,
                },
            )
        else:
            self.logger.info(
                " | ".join(log_parts),
                extra={
                    "node_name": node_name,
                    "session_id": session_id,
                    "state": state,
                },
            )


_logger_instance: Optional[CodeBuilderLogger] = None


def get_logger(**kwargs) -> CodeBuilderLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = CodeBuilderLogger(**kwargs)
    return _logger_instance
