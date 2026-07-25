# app.py
# Minimal Gradio app to explore and call methods of backend classes dynamically.
from __future__ import annotations

import ast
import dataclasses
import inspect
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Optional, Union, get_args, get_origin

import gradio as gr

# Import backend classes
from backend.accounts import AccountService
from backend.trading import TradingEngine
from backend.portfolio import PortfolioService
from backend.pricing import PricingService
from backend.transactions import TransactionLedger
from backend.validation import ValidationRules
from backend.storage import InMemoryStore


def doc_summary(obj: Any) -> str:
    doc = (obj.__doc__ or "").strip()
    if not doc:
        return ""
    first_line = doc.splitlines()[0]
    return first_line.strip()


def is_public_method(name: str, func: Any) -> bool:
    if name.startswith("_"):
        return False
    if not callable(func):
        return False
    # Skip typical dunder and representation methods just in case
    if name in {"__init__", "__repr__", "__str__"}:
        return False
    return True


def type_to_example(annotation: Any) -> Any:
    # Produce a simple example value for a given type annotation
    try:
        origin = get_origin(annotation)
        args = get_args(annotation)
    except Exception:
        origin = None
        args = ()

    if annotation is inspect._empty or annotation is Any:
        return None

    # Optional[T] == Union[T, NoneType]
    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return type_to_example(non_none[0])
        return None

    # Common primitives
    if annotation in (int,):
        return 0
    if annotation in (float,):
        return 0.0
    if annotation in (str,):
        return ""
    if annotation in (bool,):
        return False
    if annotation is Decimal:
        return "0.00"
    if annotation in (dict, Dict, Dict[str, Any]):
        return {}
    if annotation in (list, List, List[Any]):
        return []
    if annotation in (tuple, Tuple, Tuple[Any, ...]):
        return []
    # Fallback
    return None


def signature_skeleton(sig: inspect.Signature) -> Dict[str, Any]:
    # Build a kwargs dict skeleton based on signature
    result: Dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            # Encourage use of _args and normal kwargs
            continue
        if param.default is not inspect._empty:
            # Prefer default value if simple, else map to example by annotation
            default = param.default
            # Convert Decimals and dataclasses and other non-serializables to a simple value
            if isinstance(default, (int, float, str, bool)) or default is None:
                result[name] = default
            elif isinstance(default, Decimal):
                result[name] = str(default)
            else:
                # fall back to annotation example
                ex = type_to_example(param.annotation)
                result[name] = ex
        else:
            result[name] = type_to_example(param.annotation)
    return result


def pretty_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def to_jsonable(obj: Any) -> Any:
    # Convert objects (including dataclasses, Decimal, datetime) to JSON-serializable structures
    if dataclasses.is_dataclass(obj):
        return to_jsonable(dataclasses.asdict(obj))
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        new_dict: Dict[str, Any] = {}
        for k, v in obj.items():
            # JSON keys must be strings
            new_dict[str(k)] = to_jsonable(v)
        return new_dict
    if isinstance(obj, Exception):
        return {"error": f"{obj.__class__.__name__}: {str(obj)}"}
    # Primitive
    return obj


def safe_parse_params(text: str) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Parse user params input. Supports:
      - JSON object: {"a":1,"b":2}
      - Python literal dict/list via ast.literal_eval
      - Special keys:
          {"_args": [...], "a": 1}  -> positional args plus kwargs
    Returns (args_list, kwargs_dict)
    """
    text = (text or "").strip()
    if not text:
        return [], {}
    data: Any
    try:
        data = json.loads(text)
    except Exception:
        try:
            data = ast.literal_eval(text)
        except Exception:
            # As a last resort, treat as no params
            return [], {}

    if isinstance(data, list):
        return data, {}
    if isinstance(data, dict):
        args = data.pop("_args", [])
        if not isinstance(args, list):
            args = []
        return args, data
    # Fallback ignore
    return [], {}


def format_method_info(method_obj: Any) -> str:
    sig = inspect.signature(method_obj)
    doc = (method_obj.__doc__ or "").strip()
    head = f"Signature: {method_obj.__name__}{sig}"
    if not doc:
        return head
    # Show only the first paragraph to keep minimal
    first_para = doc.split("\n\n")[0].strip()
    return f"{head}\n\n{first_para}"


def build_methods_map(instance: Any) -> Dict[str, Dict[str, Any]]:
    methods: Dict[str, Dict[str, Any]] = {}
    for name, func in inspect.getmembers(instance, predicate=callable):
        if not is_public_method(name, func):
            continue
        try:
            sig = inspect.signature(func)
        except Exception:
            continue
        # Keep only methods (bound functions)
        methods[name] = {
            "callable": func,
            "signature": sig,
            "skeleton": signature_skeleton(sig),
            "info": format_method_info(func),
        }
    return dict(sorted(methods.items(), key=lambda kv: kv[0].lower()))


def skeleton_text(skeleton: Dict[str, Any]) -> str:
    # Show skeleton as pretty JSON
    return pretty_json(skeleton)


# Create instances of each backend class with default parameters
instances_registry: Dict[str, Dict[str, Any]] = {}

def register_instance(label: str, cls: Any) -> None:
    # Instantiate with defaults
    try:
        instance = cls()
    except Exception as e:
        # If default constructor fails, store the exception instead
        instance = e
    instances_registry[label] = {
        "class": cls,
        "instance": instance,
        "purpose": doc_summary(cls),
        "methods": build_methods_map(instance) if not isinstance(instance, Exception) else {},
    }


# Register all modules/classes here
register_instance("AccountService (backend.accounts)", AccountService)
register_instance("TradingEngine (backend.trading)", TradingEngine)
register_instance("PortfolioService (backend.portfolio)", PortfolioService)
register_instance("PricingService (backend.pricing)", PricingService)
register_instance("TransactionLedger (backend.transactions)", TransactionLedger)
register_instance("ValidationRules (backend.validation)", ValidationRules)
register_instance("InMemoryStore (backend.storage)", InMemoryStore)


# Gradio event handlers (generic)
def on_method_change(instance_key: str, method_name: str):
    meta = instances_registry.get(instance_key, {})
    methods = meta.get("methods", {})
    if not method_name or method_name not in methods:
        return json.dumps({}, indent=2), "Select a method"
    skel = methods[method_name]["skeleton"]
    info = methods[method_name]["info"]
    return skeleton_text(skel), info


def on_call_method(instance_key: str, method_name: str, params_text: str):
    meta = instances_registry.get(instance_key, {})
    instance = meta.get("instance")
    if isinstance(instance, Exception):
        return {"error": f"Instance not available: {instance.__class__.__name__}: {str(instance)}"}

    methods = meta.get("methods", {})
    if not method_name or method_name not in methods:
        return {"error": "No method selected"}
    func = methods[method_name]["callable"]
    args, kwargs = safe_parse_params(params_text)
    try:
        result = func(*args, **kwargs)
        return to_jsonable(result)
    except Exception as e:
        return {"error": f"{e.__class__.__name__}: {str(e)}"}


def build_methods_summary(md: Dict[str, Dict[str, Any]]) -> str:
    if not md:
        return "No callable public methods detected."
    lines = ["Available methods:"]
    for name, info in md.items():
        sig = info["signature"]
        lines.append(f"- {name}{sig}")
    return "\n".join(lines)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Backend Modules Demo") as demo:
        gr.Markdown("# Backend Modules Demo")
        gr.Markdown(
            "Minimal UI to interact with backend classes. "
            "Pick a module tab, choose a method, edit params, and call. "
            "Params accept JSON or Python literal. Use '_args' for positional arguments."
        )

        with gr.Tabs():
            for key, meta in instances_registry.items():
                cls = meta["class"]
                instance = meta["instance"]
                purpose = meta["purpose"]
                methods_map = meta["methods"]
                cls_name = getattr(cls, "__name__", str(cls))

                with gr.Tab(key):
                    gr.Markdown(f"## {cls_name}")
                    gr.Markdown(purpose or "(no description)")
                    if isinstance(instance, Exception):
                        gr.Markdown(f"Instance failed to initialize: {instance.__class__.__name__}: {str(instance)}")
                        continue

                    method_names = list(methods_map.keys())
                    default_method = method_names[0] if method_names else None

                    with gr.Row():
                        method_dd = gr.Dropdown(
                            choices=method_names,
                            value=default_method,
                            label="Method",
                            interactive=True,
                        )
                        call_btn = gr.Button("Call")

                    method_info = gr.Markdown(label="Method Info")
                    params_tb = gr.Textbox(
                        label="Params (JSON or Python literal). Use {'_args': [...], ...} for positional args.",
                        lines=8,
                        value=skeleton_text(methods_map[default_method]["skeleton"]) if default_method else "{}",
                    )
                    result_json = gr.JSON(label="Result")

                    # Summary of methods/signatures
                    gr.Markdown(build_methods_summary(methods_map))

                    # Wire events
                    method_dd.change(
                        fn=lambda m, inst_key=key: on_method_change(inst_key, m),
                        inputs=[method_dd],
                        outputs=[params_tb, method_info],
                    )
                    call_btn.click(
                        fn=lambda m, p, inst_key=key: on_call_method(inst_key, m, p),
                        inputs=[method_dd, params_tb],
                        outputs=[result_json],
                    )
                    # Initialize method info on load
                    if default_method:
                        method_info.value = methods_map[default_method]["info"]

    return demo


app = build_app()

if __name__ == "__main__":
    app.launch()