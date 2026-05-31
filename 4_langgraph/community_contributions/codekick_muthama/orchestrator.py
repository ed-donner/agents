from __future__ import annotations

import ast
import inspect
import json
import logging
import re
import traceback
from typing import Any, Callable, Dict, Optional, Tuple
from pydantic import BaseModel, ValidationError
from graph import agent
import tools as tools_module

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class WriteFileArgs(BaseModel):
    path: str
    content: str

class ReadFileArgs(BaseModel):
    path: str

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "write_file": {"fn": getattr(tools_module, "write_file", None), "arg_model": WriteFileArgs, "available": True},
    "read_file": {"fn": getattr(tools_module, "read_file", None), "arg_model": ReadFileArgs, "available": True},
    "list_files": {"fn": getattr(tools_module, "list_files", None), "arg_model": None, "available": True},
    "run_cmd": {"fn": getattr(tools_module, "run_cmd", None), "arg_model": None, "available": False},
}

JSON_OBJ_RE = re.compile(r"(\{.*\}|\[.*\])", re.DOTALL)

def extract_json(text: str) -> Optional[Any]:
    if not isinstance(text, str):
        return None
    try:
        return json.loads(text)
    except Exception:
        pass

    m = JSON_OBJ_RE.search(text)
    if not m:
        return None
    candidate = m.group(0)
    try:
        return json.loads(candidate)
    except Exception:
        return None

def is_safe_args(args: Any) -> bool:
    if args is None:
        return True
    if not isinstance(args, dict):
        return False
    for k in args.keys():
        if not isinstance(k, str) or k.startswith("__"):
            return False
    try:
        json.dumps(args)
    except Exception:
        return False
    return True

def try_parse_json_like(obj: Any) -> Tuple[bool, Optional[Any], Optional[str]]:
    if obj is None:
        return True, None, None

    if isinstance(obj, (dict, list)):
        return True, obj, None

    if isinstance(obj, str):
        s = obj.strip()
        try:
            parsed = json.loads(s)
            return True, parsed, None
        except Exception:
            pass

        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, (dict, list)):
                return True, parsed, None
        except Exception:
            pass

        if re.match(r'^\s*[\{\[]', s):
            repaired = s.replace("'", '"')
            repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
            try:
                parsed = json.loads(repaired)
                logger.warning("Repaired JSON-like string via heuristics.")
                return True, parsed, None
            except Exception:
                pass

        return False, None, "unable_to_parse_args_as_json"

    try:
        js = json.dumps(obj)
        parsed = json.loads(js)
        return True, parsed, None
    except Exception:
        return False, None, "args_not_json_serializable"

def validate_args_with_model(arg_model: Optional[type], args: Dict) -> Tuple[bool, Optional[str]]:
    if arg_model is None:
        return True, None
    try:
        arg_model.parse_obj(args)
        return True, None
    except ValidationError as e:
        return False, str(e)

def safe_call_tool(tool_id: str, args: Optional[Dict]) -> Dict[str, Any]:
    entry = TOOL_REGISTRY.get(tool_id)
    if entry is None:
        return {"ok": False, "error": "unknown_tool", "message": f"Tool '{tool_id}' is not in the registry."}

    if not entry.get("available", False):
        return {"ok": False, "error": "tool_unavailable", "message": f"Tool '{tool_id}' is currently unavailable."}

    fn: Callable = entry.get("fn")
    if not callable(fn):
        return {"ok": False, "error": "no_callable", "message": f"Tool '{tool_id}' has no executable function."}

    ok, parsed_args, parse_err = try_parse_json_like(args)
    if not ok:
        return {
            "ok": False,
            "error": "invalid_args_format",
            "message": parse_err,
            "raw_args": args,
        }

    if parsed_args is None:
        parsed_args = {}

    if not isinstance(parsed_args, dict):
        return {
            "ok": False,
            "error": "invalid_args_type",
            "message": "Tool 'args' must be a JSON object/dict.",
            "parsed_args_type": type(parsed_args).__name__,
        }

    if not is_safe_args(parsed_args):
        return {"ok": False, "error": "invalid_args", "message": "Arguments failed safety checks (must be dict, JSON-serializable, no dunder keys)."}

    arg_model = entry.get("arg_model")
    valid, err = validate_args_with_model(arg_model, parsed_args or {})
    if not valid:
        return {"ok": False, "error": "arg_validation_failed", "message": err}

    try:
        sig = inspect.signature(fn)
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            result = fn(**(parsed_args or {}))
        else:
            param_names = [p.name for p in sig.parameters.values() if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)]
            call_args = []
            for name in param_names:
                if name in (parsed_args or {}):
                    call_args.append(parsed_args[name])
            result = fn(*call_args)
        return {"ok": True, "result": result}
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("Exception while calling tool %s", tool_id)
        return {"ok": False, "error": "exception_during_tool", "message": str(e), "traceback": tb}

def run_with_orchestration(user_prompt: str, *, recursion_limit: int = 1, agent_kwargs: Optional[Dict] = None) -> Dict[str, Any]:
    agent_kwargs = agent_kwargs or {}
    out: Dict[str, Any] = {"ok": False, "agent_raw": None, "parsed_invocation": None, "tool_result": None, "error": None}

    raw = None
    try:
        if hasattr(agent, "invoke"):
            agent.invoke(
                {"user_prompt": user_prompt},
                {"recursion_limit": recursion_limit}
            )
        else:
            raw = agent(user_prompt, **agent_kwargs)

        out["agent_raw"] = raw

        parsed = None
        if isinstance(raw, dict):
            parsed = raw
        elif isinstance(raw, str):
            parsed = extract_json(raw)

        if parsed is None:
            out.update({"ok": True, "parsed_invocation": None, "tool_result": None})
            return out

        if not isinstance(parsed, dict):
            out["error"] = "parsed_not_object"
            return out

        tool_id = parsed.get("tool")
        args = parsed.get("args", None)

        out["parsed_invocation"] = {"tool": tool_id, "args": args}

        if tool_id is None:
            out.update({"ok": True, "tool_result": None})
            return out

        if tool_id not in TOOL_REGISTRY:
            logger.warning("Unknown tool requested: %s. Skipping execution.", tool_id)
            out["tool_result"] = {
                "ok": True,
                "result": {
                    "status": "skipped",
                    "message": f"Tool '{tool_id}' is not recognized. No action taken.",
                },
            }
            out["ok"] = True
            out["error"] = None
            return out

        tool_result = safe_call_tool(tool_id, args)
        out["tool_result"] = tool_result
        out["ok"] = tool_result.get("ok", False)
        if not out["ok"] and out["error"] is None:
            out["error"] = "tool_execution_failed"
        return out

    except Exception as e:
        out["agent_raw"] = raw
        out["error"] = "exception_in_orchestrator"
        out["error_message"] = str(e)
        out["traceback"] = traceback.format_exc()
        logger.exception("Exception in orchestrator while handling prompt")
        return out
