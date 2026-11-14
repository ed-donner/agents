import json
from typing import Any


class FlowTriggerError(RuntimeError):
    """Raised when the flow trigger payload cannot be read."""


def parse_trigger_payload(raw_payload: str) -> dict[str, Any]:
    """Parse a trigger payload and require a JSON object."""
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise FlowTriggerError("Invalid JSON payload provided as argument") from exc

    if not isinstance(payload, dict):
        raise FlowTriggerError("Trigger payload must be a JSON object")

    return payload
