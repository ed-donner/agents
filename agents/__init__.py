"""Lightweight stub for the project-specific `agents` API.

This package provides minimal definitions that the example scripts in
this workspace depend on.  The real implementation lives outside of
this repo or is not needed for the demonstration code, so we expose
simple no-op placeholders here to satisfy imports and the type checker.

Adding this package to the workspace root causes Python to resolve
`import agents` locally instead of pulling in the unrelated PyPI
`agents` project (which conflicts and is heavy).  It also lets VS Code
and Pylance find symbols while editing.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def function_tool(func: F | None = None) -> F | Callable[[F], F]:
    """Decorator used by example agents to mark a function as a tool.

    This stub simply returns the original callable unchanged so that
    code executes normally.  In a real implementation the decorator
    would register metadata and perform runtime integration.
    """
    if func is None:
        def decorator(f: F) -> F:  # type: ignore[no-untyped-def]
            return f
        return decorator  # type: ignore[return-value]
    return func  # type: ignore[return-value]


# Additional placeholders exposed in examples.  They are empty classes
# so that imports succeed and isinstance/type checks behave.

class Agent:
    """Base class for agents (no functionality in stub)."""
    pass


class OpenAIChatCompletionsModel:
    """Stub for the OpenAI chat completions wrapper."""
    pass
